from pudb import remote

def set_trace():
    remote.set_trace(term_size=(200, 50))
