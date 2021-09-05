import numpy as np
from tunable import Tunable


class Seed(Tunable):
    """Seed for the random number generator"""

    default = 1


class RandomNumberGenerator(Tunable):
    """Random number generator to be used"""

    @classmethod
    def available_rngs(cls):
        members = [getattr(np.random, name) for name in dir(np.random)]
        members = [member for member in members if isinstance(member, type)]
        members = [
            member for member in members if np.random.BitGenerator in member.__bases__
        ]
        members = {member.__name__: member for member in members}
        return members

    @classmethod
    def get(cls):
        return cls.available_rngs()[cls.value]

    @classmethod
    def test(cls, value):
        return value in cls.available_rngs()

    default = 'PCG64'


class RRF:
    """Reproducible random function"""

    seed_value = 0

    def __init__(self, mode='callable'):
        assert mode in (
            'callable',
            'iterator',
        )
        self.mode = mode

    def __getattr__(self, item):
        gen = self.spawn_generator()
        func = getattr(gen, item)

        if self.mode == 'iterator':

            def _inner(*args, **kwargs):
                while True:
                    yield func(*args, **kwargs)

        else:

            def _inner(*args, **kwargs):
                def _inner_inner():
                    return func(*args, **kwargs)

                return _inner_inner

        return _inner

    @classmethod
    def seed(cls, seed=None):
        if seed is None:
            seed = Seed.value
        cls.seed_value = seed
        cls.seed_sequence = np.random.SeedSequence(cls.seed_value)
        cls.generator = cls(mode='callable')
        cls.sequence = cls(mode='iterator')
        return seed

    @classmethod
    def spawn_generator(cls):
        seed = cls.seed_sequence.spawn(1)[0]

        rng = RandomNumberGenerator.get()

        return np.random.Generator(bit_generator=rng(seed=seed))

    @classmethod
    def wrap(cls, sequence, func):
        while True:
            yield func(next(sequence))

    @classmethod
    def compose(cls, func, **kwargs):
        while True:
            used_kwargs = {key: next(value) for key, value in kwargs.items()}
            yield func(**used_kwargs)

    @classmethod
    def chain(cls, func, **kwargs):
        while True:
            yield from func(**kwargs)


def enforce_bounds(iterator, minimum=-np.Inf, maximum=np.Inf):
    for value in iterator:
        if np.isscalar(value):
            if maximum > value > minimum:
                yield value
        else:
            if ((maximum > np.array(value)) & (np.array(value) > minimum)).all():
                yield value
