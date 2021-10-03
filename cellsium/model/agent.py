"""Cell model classes and routines, general."""
from copy import deepcopy
from typing import Any, List

from ..random import RRF
from ..typing import DefaultsType


def iter_through_class_hierarchy(cls: type) -> List[type]:
    """
    Iterate thru a class hierarchy and return all bases.

    :param cls: Type
    :return: List of bases
    """
    collector = []

    def _inner(cls_):
        if cls_ == object:
            return
        for base in cls_.__bases__:
            collector.append(base)
            _inner(base)

    _inner(cls)
    return collector


class InitializeWithParameters:
    """Mixin for objects with defaults."""

    def __init__(self, **kwargs):
        for cls_ in iter_through_class_hierarchy(self.__class__):
            if hasattr(cls_, 'defaults'):
                for k, v in cls_.defaults().items():
                    if hasattr(v, '__call__'):
                        v = v()
                    setattr(self, k, v)

        for k, v in kwargs.items():
            setattr(self, k, v)


class WithRandomSequences:
    """Mixin for objects with random sequences."""

    all_random_sequences_generated_for = {}

    @classmethod
    def get_random_sequences(cls, sequence: Any = None) -> Any:
        if sequence is not None and cls in cls.all_random_sequences_generated_for:
            del cls.all_random_sequences_generated_for[cls]

        if cls not in cls.all_random_sequences_generated_for:
            all_random_sequences = {}
            if sequence is None:
                sequence = RRF.sequence
            for cls_ in iter_through_class_hierarchy(cls):
                if hasattr(cls_, 'random_sequences'):
                    for key, value in cls_.random_sequences(sequence).items():
                        all_random_sequences[key] = value

            cls.all_random_sequences_generated_for[cls] = all_random_sequences

        return cls.all_random_sequences_generated_for[cls]

    @property
    def random(self) -> Any:
        class _Proxy:
            def __init__(self, backing):
                self.backing = backing

            def __getattr__(self, item):
                return self.backing[item]

        return _Proxy(self.get_random_sequences())


class Copyable:
    """Mixin for copyable objects."""

    def copy(self) -> "Copyable":
        return deepcopy(self)


class Representable:
    """Mixins for adding a repr implementation."""

    def __repr__(self):
        return (
            self.__class__.__name__
            + '('
            + ', '.join(['%s=%r' % (k, v) for k, v in sorted(self.__dict__.items())])
            + ')'
        )


class IdCounter:
    """Id provider singleton class."""

    id_counter: int = 0

    @classmethod
    def next_cell_id(cls) -> int:
        cls.id_counter += 1
        return cls.id_counter

    @classmethod
    def reset(cls) -> None:
        cls.id_counter = 0


class WithLineage:
    """Mixin providing lineage tracking."""

    def copy(self) -> "WithLineage":
        copy = super().copy()
        copy.next_cell_id()
        return copy

    # noinspection PyAttributeOutsideInit
    def next_cell_id(self) -> None:
        self.id_ = IdCounter.next_cell_id()

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(id_=lambda: IdCounter.next_cell_id(), parent_id=0)


class WithLineageHistory:
    """Mixin providing lineage history."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(lineage_history=lambda: [0])


class WithTemporalLineage:
    """Mixing providing temporal lineage history."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(birth_time=0.0)


__all__ = [
    'InitializeWithParameters',
    'WithRandomSequences',
    'Copyable',
    'Representable',
    'IdCounter',
    'WithLineage',
    'WithLineageHistory',
    'WithTemporalLineage',
]
