import numpy as np

from tunable import Tunable

from .random import RRF
from . import Width, Height


class RandomlyDistributed(Tunable):
    pass

# class RandomDistribution(Tunable):
#     default = 'normal'
#
#     @classmethod
#     def test(cls, value):
#         return cls.get(value)
#
#     @classmethod
#     def get(cls):
#         return getattr(np.random, value, False)


class Seed(Tunable):
    default = '1'


class NewCellCount(Tunable): default = 1


class NewCellRadiusFromCenter(RandomlyDistributed): default = 5.0


class NewCellWidthMean(RandomlyDistributed): default = 1.0


class NewCellWidthStd(RandomlyDistributed): default = 0.1


class NewCellWidthAbsoluteMax(Tunable): default = 1.5


class NewCellWidthAbsoluteMin(Tunable): default = 0.75


class NewCellLength1Mean(RandomlyDistributed): default = 2.5


class NewCellLength1Std(RandomlyDistributed): default = 0.15


class NewCellLength2Mean(RandomlyDistributed): default = 1.25


class NewCellLength2Std(RandomlyDistributed): default = 0.15


class NewCellLengthAbsoluteMax(Tunable): default = 3.5


class NewCellLengthAbsoluteMin(Tunable): default = 0.8


class NewCellBendOverallLower(RandomlyDistributed): default = -0.1


class NewCellBendOverallUpper(RandomlyDistributed): default = 0.1


class NewCellBendUpperLower(RandomlyDistributed): default = -0.1


class NewCellBendUpperUpper(RandomlyDistributed): default = 0.1


class NewCellBendLowerLower(RandomlyDistributed): default = -0.1


class NewCellBendLowerUpper(RandomlyDistributed): default = 0.1


def enforce_bounds(iterator, minimum=-np.Inf, maximum=np.Inf):
    for value in iterator:
        if np.isscalar(value):
            if maximum > value > minimum:
                yield value
        else:
            if ((maximum > np.array(value)) & (np.array(value) > minimum)).all():
                yield value


class CellParameterGenerator(object):
    def __init__(self):
        assert NewCellLength1Mean.value > NewCellWidthMean.value
        assert NewCellLength2Mean.value > NewCellWidthMean.value

        length_raw = enforce_bounds(RRF.new(
            np.random.multivariate_normal,
            [NewCellLength1Mean.value, NewCellLength2Mean.value], [
                [NewCellLength1Std.value, 0.0],
                [0.0, NewCellLength2Std.value]
            ]),
            minimum=NewCellLengthAbsoluteMin.value,
            maximum=NewCellLengthAbsoluteMax.value)

        self.length = RRF.new(lambda: float(next(length_raw)[np.random.randint(0, 1)]))

        self.width = enforce_bounds(
            RRF.new(np.random.normal, NewCellWidthMean.value, NewCellWidthStd.value),
            minimum=NewCellWidthAbsoluteMin.value,
            maximum=NewCellWidthAbsoluteMax.value)

        self.bend_overall = RRF.new(np.random.uniform, NewCellBendOverallLower.value, NewCellBendOverallUpper.value)
        self.bend_upper = RRF.new(np.random.uniform, NewCellBendUpperLower.value, NewCellBendUpperUpper.value)
        self.bend_lower = RRF.new(np.random.uniform, NewCellBendLowerLower.value, NewCellBendLowerUpper.value)

        def _position():
            radius = np.random.uniform(0, NewCellRadiusFromCenter.value)
            angle = np.radians(np.random.uniform(0, 360.0))
            return [radius * np.cos(angle) + Width.value/2, radius * np.sin(angle) + Height.value/2]

        self.position = RRF.new(_position)

        # does it make sense to make the angle configurable?
        self.angle = RRF.new(lambda: float(np.radians(np.random.uniform(0, 360.0))))
