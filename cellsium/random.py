import numpy as np
import binascii


class RRF(object):
    """ Reproducible random function """
    seed_state = np.random.get_state()

    @classmethod
    def seed(cls, seed):
        np.random.seed(binascii.crc32(seed.encode()) & 0xffffffff)
        cls.seed_state = np.random.get_state()

    @classmethod
    def new(cls, fun, *args, **kwargs):
        state = cls.seed_state
        while True:
            np.random.set_state(state)
            value = fun(*args, **kwargs)
            state = np.random.get_state()
            yield value
