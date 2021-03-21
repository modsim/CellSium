from copy import deepcopy

from ..random import RRF


def iter_through_class_hierarchy(cls):
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

    all_random_sequences_generated_for = {}

    @classmethod
    def get_random_sequences(cls, sequence=None):
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
    def random(self):
        class _Proxy:
            def __init__(self, backing):
                self.backing = backing

            def __getattr__(self, item):
                return self.backing[item]

        return _Proxy(self.get_random_sequences())


class Copyable:
    def copy(self):
        return deepcopy(self)


class Representable:
    def __repr__(self):
        return (
            self.__class__.__name__
            + '('
            + ', '.join(['%s=%r' % (k, v) for k, v in sorted(self.__dict__.items())])
            + ')'
        )


class IdCounter:
    id_counter = 0

    @classmethod
    def next_cell_id(cls):
        cls.id_counter += 1
        return cls.id_counter

    @classmethod
    def reset(cls):
        cls.id_counter = 0


class WithLineage:
    def copy(self):
        copy = super().copy()
        copy.next_cell_id()
        return copy

    # noinspection PyAttributeOutsideInit
    def next_cell_id(self):
        self.id_ = IdCounter.next_cell_id()

    @staticmethod
    def defaults():
        return dict(id_=lambda: IdCounter.next_cell_id(), parent_id=0)


class WithLineageHistory:
    @staticmethod
    def defaults():
        return dict(lineage_history=lambda: [0])


class WithTemporalLineage:
    @staticmethod
    def defaults():
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
