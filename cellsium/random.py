import binascii

import numpy as np


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


def enforce_bounds(iterator, minimum=-np.Inf, maximum=np.Inf):
    for value in iterator:
        if np.isscalar(value):
            if maximum > value > minimum:
                yield value
        else:
            if ((maximum > np.array(value)) & (np.array(value) > minimum)).all():
                yield value
