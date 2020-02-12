from pynfb.signal_processing.filters import BaseFilter
import numpy as np

class MyFilterSequence(BaseFilter):
    def __init__(self, filter_sequence):
        self.sequence = filter_sequence

    output = []
    def apply(self, chunk: np.ndarray):
        for filter_ in self.sequence:
            chunk = filter_.apply(chunk)
            output.append(chunk)
        return output
