from copy import deepcopy


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


class Copyable(object):
    def copy(self):
        return deepcopy(self)


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
