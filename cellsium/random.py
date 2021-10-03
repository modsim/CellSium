"""Random number generation infrastructure."""
from typing import Dict, Iterable, Iterator, Type, Union

import numpy as np
from tunable import Tunable

from .typing import AnyFunction, KwargFunction


class Seed(Tunable):
    """Seed for the random number generator"""

    default: int = 1


class RandomNumberGenerator(Tunable):
    """Random number generator to be used"""

    @classmethod
    def available_rngs(cls) -> Dict[str, Type[np.random.BitGenerator]]:
        members = [getattr(np.random, name) for name in dir(np.random)]
        members = [member for member in members if isinstance(member, type)]
        members = [
            member for member in members if np.random.BitGenerator in member.__bases__
        ]
        members = {member.__name__: member for member in members}
        return members

    @classmethod
    def get(cls) -> Type[np.random.BitGenerator]:
        return cls.available_rngs()[cls.value]

    @classmethod
    def test(cls, value: str) -> bool:
        return value in cls.available_rngs()

    default: str = "PCG64"


class RRF:
    """Reproducible random function."""

    seed_value: int = 0

    def __init__(self, mode: str = "callable"):
        assert mode in (
            "callable",
            "iterator",
        )
        self.mode = mode

    def __getattr__(self, item):
        gen = self.spawn_generator()
        func = getattr(gen, item)

        if self.mode == "iterator":

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
    def seed(cls, seed: int = None) -> int:
        """
        Set the seed for the RRF.

        :param seed: Seed
        :return: Seed
        """
        if seed is None:
            seed = Seed.value
        cls.seed_value = seed
        cls.seed_sequence = np.random.SeedSequence(cls.seed_value)
        cls.generator = cls(mode="callable")
        cls.sequence = cls(mode="iterator")
        return seed

    @classmethod
    def spawn_generator(cls) -> np.random.Generator:
        """
        Generates a new np.random.Generator from
        the seed and the configured bitgenerator.

        :return: The Generator instance
        """
        seed = cls.seed_sequence.spawn(1)[0]

        rng = RandomNumberGenerator.get()

        return np.random.Generator(bit_generator=rng(seed=seed))

    @classmethod
    def wrap(cls, sequence: Iterable, func: AnyFunction) -> Iterator:
        """
        Wraps the sequence with the function func so that
        each returned element x becomes func(x).

        :param sequence: Input sequence
        :param func: Function to be called
        :return: Iterator of values
        """
        while True:
            yield func(next(sequence))

    @classmethod
    def compose(cls, func: KwargFunction, **kwargs) -> Iterator:
        """
        Calls a function func with an element \
        of the sequences from the kwargs as kwargs.

        :param func: Function to be called
        :param kwargs: Kwargs of sequences, of which an element each \
        will be used for each function call
        :return: Iterator of values
        """
        while True:
            used_kwargs = {key: next(value) for key, value in kwargs.items()}
            yield func(**used_kwargs)

    @classmethod
    def chain(cls, func: KwargFunction, **kwargs) -> Iterator:
        """
        Calls func with kwargs and yields from it.

        :param func: Function to call
        :param kwargs: Kwargs to pass
        :return: Iterator of values
        """
        while True:
            yield from func(**kwargs)


def enforce_bounds(
    iterator: Iterator, minimum: float = -np.Inf, maximum: float = np.Inf
) -> Iterator[Union[float, np.ndarray]]:
    """
    Will iter thru an iterator til a value is within bounds.
    For arrays, all values will be considered.

    :param iterator: Iterator
    :param minimum: Minimum value
    :param maximum: Maximum value
    :return: An iterator of values within bounds
    """
    for value in iterator:
        if np.isscalar(value):
            if maximum > value > minimum:
                yield value
        else:
            if ((maximum > np.array(value)) & (np.array(value) > minimum)).all():
                yield value
