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


class InitializeWithParameters(object):
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
    @classmethod
    def get_random_sequences(cls, sequence=None):
        if hasattr(cls, 'all_random_sequences'):
            return cls.all_random_sequences
        cls.all_random_sequences = {}
        if sequence is None:
            sequence = RRF.sequence
        for cls_ in iter_through_class_hierarchy(cls):
            if hasattr(cls_, 'random_sequences'):
                cls.all_random_sequences.update(cls_.random_sequences(sequence))
        return cls.all_random_sequences

    @property
    def random(self):
        class _Proxy:
            def __init__(self, backing):
                self.backing = backing

            def __getattr__(self, item):
                return self.backing[item]

        return _Proxy(self.get_random_sequences())


class Copyable(object):
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


_id_counter = 0


def next_cell_id():
    global _id_counter
    _id_counter += 1
    return _id_counter


class WithLineage(object):
    def copy(self):
        copy = super(WithLineage, self).copy()
        copy.next_cell_id()
        return copy

    # noinspection PyAttributeOutsideInit
    def next_cell_id(self):
        self.id_ = next_cell_id()

    @staticmethod
    def defaults():
        return dict(id_=lambda: next_cell_id(), parent_id=0)


class WithLineageHistory(object):
    @staticmethod
    def defaults():
        return dict(lineage_history=lambda: [0])


class WithTemporalLineage(object):
    @staticmethod
    def defaults():
        return dict(birth_time=0.0)
