# ampdecorator.py
# Copyright (C) 2013  Bastian Venthur
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


"""
This module provides the :class:`AmpDecorator` class.

As a user, it is very unlikely that you'll have to deal with it
directly. Its main purpose is to add additional functionality to the low
level amplifier drivers. This functionality includes features like:
saving data to a file. or being able to receive marker via network
(TCP/IP and UDP).

By using the :func:`libmushu.__init__.get_amp` method, you'll
automatically receive decorated amplifiers.

"""


from __future__ import division

# import select
import socket
import time
from multiprocessing import Process, Queue, Event
import os
import signal
import struct
import json
import logging


# warning: dirty hack to shut down the event loop.
import subprocess
import signal

# we may not need those anymore
import asyncore
import asynchat

# we definitely need this -- I don't know why it's greyed out here.
import asyncio

from libmushu.amplifier import Amplifier

logger = logging.getLogger(__name__)
logger.info('Logger started')


END_MARKER = '\n'
BUFSIZE = 2**16
PORT = 32344


class AmpDecorator(Amplifier):
    """This class 'decorates' the Low-Level Amplifier classes with
    Network-Marker and Save-To-File functionality.

    You use it by decorating (not as in Python-Decorator, but in the GoF
    sense) the low level amplifier class you want to use::

        import libmushu
        from libmushu.ampdecorator import AmpDecorator
        from libmushu.driver.randomamp import RandomAmp

        amp = Ampdecorator(RandomAmp)

    Waring: The network marker timings on Windows have a resolution of
    10ms-15ms. On Linux the resolution is 1us. This is due to
    limitations of Python's time.time method, or rather a Windows
    specific issue.

    There exists currently no precise timer, providing times which are
    comparable between two running processes on Windows. The performance
    counter provided on Windows, has a much better resolution but is
    relative to the processes start time and it drifts (1s per 100s), so
    it is only precise for a relatively short amount of time.

    If a higher precision is needed one has to replace the time.time
    calls with something which provides a better precision. For example
    one could create a third process which provides times or regularly
    synchronize both processes with the clock synchronization algorithm
    as described here:

        http://en.wikipedia.org/wiki/Network_Time_Protocol

    Alternatively one could use `timeGetTime` from Windows' Multi Media
    library, which is tunable via `timeBeginPeriod` and provides a
    precision of 1-2ms. Apparently this is the way Chrome and many
    others do it.::

        from __future__ import division

        from ctypes import windll
        import time

        timeBeginPeriod = windll.winmm.timeBeginPeriod
        timeEndPeriod = windll.winmm.timeEndPeriod
        timeGetTime = windll.winmm.timeGetTime

        if __name__ == '__main__':
            # wrap the code that needs high precision in timeBegin- and
            # timeEndPeriod with the same parameter. The parameter is
            # the interval in ms you want as precision. Usually the
            # minimum value allowed is 1 (best).
            timeBeginPeriod(1)
            times = []
            t_start = time.time()
            while time.time() < (time.time() + 1):
                times.append(timeGetTime())
            times = sorted(list(set(times)))
            print(1000 / len(times))
            timeEndPeriod(1)

    """

    def __init__(self, ampcls):
        self.amp = ampcls()
        self.write_to_file = False

    @property
    def presets(self):
        return self.amp.presets

    def start(self, filename=None, **kwargs):
        # prepare files for writing
        self.write_to_file = False
        if filename is not None:
            self.write_to_file = True
            filename_marker = filename + '.marker'
            filename_eeg = filename + '.eeg'
            filename_meta = filename + '.meta'
            for filename in filename_marker, filename_eeg, filename_meta:
                if os.path.exists(filename):
                    logger.error('A file "%s" already exists, aborting.' % filename)
                    raise Exception
            self.fh_eeg = open(filename_eeg, 'wb')
            self.fh_marker = open(filename_marker, 'w')
            self.fh_meta = open(filename_meta, 'w')
            # write meta data
            meta = {'Channels': self.amp.get_channels(),
                    'Sampling Frequency': self.amp.get_sampling_frequency(),
                    'Amp': str(self.amp)
                    }
            json.dump(meta, self.fh_meta, indent=4)

        # start the marker server
        self.marker_queue = Queue()
        self.tcp_reader_running = Event()
        self.tcp_reader_running.set()
        tcp_reader_ready = Event()
        self.stoploopev = Event()
        self.tcp_reader = Process(target=marker_reader,
                                  args=(self.marker_queue,
                                        self.tcp_reader_running,
                                        tcp_reader_ready,
                                        self.stoploopev,
                                        PORT
                                        )
                                  )
        self.tcp_reader.start()
        logger.debug('Waiting for marker server to become ready...')
        tcp_reader_ready.wait()
        logger.debug('Marker server is ready.')
        # zero the sample counter
        self.received_samples = 0
        # start the amp --> hopefully this'll work?
        self.amp.start(**kwargs)

    def stop(self):
        # stop the amp
        self.amp.stop()
        # stop the marker server
        self.tcp_reader_running.clear()

        logger.debug('Waiting for marker server process to stop...')
        # logger.debug('Using Dirty Hack and Send a KeyboardInterrupt (Linux Only for now): ...')

        # try to send a keyboard CTRL-C to the process...
        # well, I could try to do this more nicely.
        #pid = self.tcp_reader.pid
        #os.kill(pid, signal.SIGINT)  # keyboardinterrupt might hang things...
        self.stoploopev.set()   # this should now more cleanly stop the ev loop in the Process, since this ev/byte is SHARED
                                # between the two processes. Like in DataCurator.

        self.tcp_reader.join()
        logger.debug('Marker server process stopped.')
        # close the files
        if self.write_to_file:
            logger.debug('Closing files.')
            for fh in self.fh_eeg, self.fh_marker, self.fh_meta:
                fh.close()
        print('amplifier stopped!')

    def configure(self, *args, **kwargs):
        self.amp.configure(*args, **kwargs)

    def get_data(self):
        """Get data from the amplifier.

        This method is supposed to get called as fast as possible (i.e
        hundreds of times per seconds) and returns the data and the
        markers.

        Returns
        -------
        data : 2darray
            a numpy array (time, channels) of the EEG data
        markers : list of (float, str)
            a list of markers. Each element is a tuple of timestamp and
            string. The timestamp is the time in ms relative to the
            onset of the block of data. Note that negative values are
            *allowed* as well as values bigger than the length of the
            block of data returned. That is to be interpreted as a
            marker from the last block and a marker for a future block
            respectively.

        """
        # get data and marker from underlying amp
        ampout = self.amp.get_data()

        if len(ampout) == 2:
            data, marker = ampout
            annotations = None
        elif len(ampout) == 3:
            data, marker, annotations = ampout



        t = time.time()
        # length in sec of the new block according to #samples and fs
        block_duration = len(data) / self.amp.get_sampling_frequency()
        # abs time of start of the block
        t0 = t - block_duration
        # duration of all blocks in ms except the current one
        duration = 1000 * self.received_samples / self.amp.get_sampling_frequency()

        # our markers are relative to the start of the current ASKED block of data, in seconds.
        # it needs to be in msec.
        lpt_marker = []
        while len(marker) > 0:
            # but we can just multiply with 1000, to fix things.
            tmarker=marker.pop(0)
            lpt_marker.append((tmarker[0], tmarker[1]))  # this is just BP!
            #print('duration', duration)
            # print(tmarker[0])
            # print(duration)
            #print('+marker', duration + tmarker[0]*5000)

        # print(lpt_marker)
        # merge markers
        tcp_marker = []
        while not self.marker_queue.empty():
            m = self.marker_queue.get()
            print(m)
            m[0] = (m[0] - t0) * 1000
            tcp_marker.append(m)
        marker = sorted(lpt_marker + tcp_marker)
        # save data to files
        if self.write_to_file:
            for m in marker:
                self.fh_marker.write("%f %s\n" % (duration + m[0], m[1]))
            self.fh_eeg.write(struct.pack("f"*data.size, *data.flatten()))
        self.received_samples += len(data)
        # print(len(data))
        # print(self.received_samples)
        if len(data) == 0 and len(marker) > 0:
            logger.error('Received marker but no data. This is an error, the amp should block on get_data until data is available. Marker timestamps will be unreliable.')

        if len(ampout) == 2:
            return data, marker
        elif len(ampout) == 3:
            return data, marker, annotations

    def get_channels(self):
        return self.amp.get_channels()

    def get_sampling_frequency(self):
        return self.amp.get_sampling_frequency()


def handle_data(queue, data, begintime):
    # do the time-stamp thingy + put it into the queue.
    timestamp = time.time() - begintime
    markertext = data.decode("utf-8")
    queue.put([timestamp, markertext])
    # print("%d" % queue.qsize())

    item=queue.get()
    queue.put(item)
    # print(item)


def marker_reader(queue, running, ready, stoploopev, PORT):
    # define our UDP class , which includes what to actually DO with the data:
    # this also kind-of uses the async/await stuff!


    # so if I wanna pass stuff on to a queue, I'd have to give the queue as an input argument, so we can put stuff on it, right?
    # put the queue in dunder init
    # why isn't this subclassed?
    # copy/paste the following from the examples on asyncio in python docs. We also tested these.
    class EchoServerProtocol(asyncio.DatagramProtocol):
        # i'll just define a setter method to pass on the queue. Man.
        def __init__(self, queue):
            self.queue = queue

        def set_queue(self, queue):
            self.queue.queue

        def connection_made(self, transport):
            self.transport = transport

        def datagram_received(self, data, addr):
            message = data.decode()
            # print('Received %r from %s' % (message, addr))
            # print('Send %r to %s' % (message, addr))
            # self.transport.sendto(data, addr)

            # so -- instead of echo-ing some stuff -- move the queue forward to
            # -- or IN ADDITION TO echo-ing --> handle the data.
            # data handler, along with the data.
            handle_data(queue, data, begin_time)

    # Define also the TCP class, with also a 'data handler'
    # put the queue in dunder init
    class EchoServerClientProtocol(asyncio.Protocol):
        def __init__(self, queue):
            self.queue = queue

        def set_queue(self, queue):
            self.queue = queue

        def connection_made(self, transport):
            peername = transport.get_extra_info('peername')
            print('Connection from {}'.format(peername))
            self.transport = transport

        def data_received(self, data):
            message = data.decode()
            print('Data received: {!r}'.format(message))

            print('Send: {!r}'.format(message))
            self.transport.write(data)

            print('Close the client socket')
            self.transport.close()

            # OK and then:
            handle_data(queue, data, begin_time)

    # get our event loop from asyncio -- not our own event loop stuff as shown in the youtube video:
    # it's still a bit esotheric.
    loop = asyncio.new_event_loop()
    begin_time = time.time()

    # add stuff to the loop. First the UDP:
    # One protocol instance will be created to serve all client requests
    # transport is a coroutine?
    #if verbose:
    #    print("Starting UDP server")
    listen = loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(queue), local_addr=('127.0.0.1', PORT))
    transport, protocol = loop.run_until_complete(listen)

    # then the TCP: -- why one is called a coro, and another is called 'listen', I do not know.
    # I also wish to check whether
    #if verbose:
    #    print("Starting TCP server")
    # the docs of asyncio are abhorrent. According to docs, this returns a server object.
    # but a server object is apparently also a coroutine?
    import socket, errno

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", PORT))
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            print("Port {} is already in use".format(PORT))
            return
        else:
            # something else raised the socket.error exception
            # print(e)
            pass
    s.close()

    print('starting markerserver on port: {}'.format(PORT))
    coro = loop.create_server(lambda: EchoServerClientProtocol(queue), '127.0.0.1', PORT)
    server = loop.run_until_complete(coro)

    # figure out how to add something to this loop that'll neatly exit it.
    # hmmm... we CAN change things so that TCP and UDP should use different ports.
    # do UDP and TCP use different ports to begin with??
    # OK... so this works quite well. Was easier than I thought. It all works nicely concurrently, too.
    # so I just need to Methodify this, match to what's written in mushu, and pass on the multiprocessing queue?

    # define a coroutine, add it to the loop, too...
    async def check_stop_loop(loop, stoploopev):
        while not stoploopev.is_set():
            await asyncio.sleep(0.00001)
        # print('stopping!')
        loop.call_soon_threadsafe(loop.stop)

    loop.create_task(check_stop_loop(loop, stoploopev))
    # try that...

    # say that we're ready.
    ready.set()

    # print("starting...")

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass



    # print("stopping ampdecorator, I")

    # closing statements -- do we need those?:
    # close the transport:
    # transport.close() .. hmm apparently, we won't have to 'close' the transport?
    # loop.run_until_complete(transport.wait_closed()) # does this make sense --> NO

    # Close the server
    # TCP:
    server.close()
    # print("stopping ampdecorator, II")
    loop.run_until_complete(server.wait_closed())

    # print("stopping ampdecorator, III")
    # close the loop, plz?
    loop.close()
    print('stopped markerserver on: {}'.format(PORT))

    # print("stopping ampdecorator, IV")
