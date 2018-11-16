import numpy as np

from tunable import Tunable

from .random import RRF, enforce_bounds


class RandomlyDistributed(Tunable):
    pass


class Seed(Tunable):
    default = '1'


class NewCellCount(Tunable):
    default = 1


class NewCellRadiusFromCenter(RandomlyDistributed):
    default = 5.0


class NewCellWidthMean(RandomlyDistributed):
    default = 1.0


class NewCellWidthStd(RandomlyDistributed):
    default = 0.1


class NewCellWidthAbsoluteMax(Tunable):
    default = 1.5


class NewCellWidthAbsoluteMin(Tunable):
    default = 0.75


class NewCellLength1Mean(RandomlyDistributed):
    default = 2.5


class NewCellLength1Std(RandomlyDistributed):
    default = 0.15


class NewCellLength2Mean(RandomlyDistributed):
    default = 1.25


class NewCellLength2Std(RandomlyDistributed):
    default = 0.15


class NewCellLengthAbsoluteMax(Tunable):
    default = 3.5


class NewCellLengthAbsoluteMin(Tunable):
    default = 0.8


class NewCellBendOverallLower(RandomlyDistributed):
    default = -0.1


class NewCellBendOverallUpper(RandomlyDistributed):
    default = 0.1


class NewCellBendUpperLower(RandomlyDistributed):
    default = -0.1


class NewCellBendUpperUpper(RandomlyDistributed):
    default = 0.1


class NewCellBendLowerLower(RandomlyDistributed):
    default = -0.1


class NewCellBendLowerUpper(RandomlyDistributed):
    default = 0.1


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
            return [float(radius * np.cos(angle) + Width.value/2), float(radius * np.sin(angle) + Height.value/2)]

        self.position = RRF.new(_position)

        # does it make sense to make the angle configurable?
        self.angle = RRF.new(lambda: float(np.radians(np.random.uniform(0, 360.0))))


class Width(Tunable):
    default = 40.0


class Height(Tunable):
    default = 60.0


class Calibration(Tunable):
    default = 0.065


def pixel_to_um(pix):
    return pix * Calibration.value


def um_to_pixel(um):
    return um / Calibration.value


def h_to_s(hours):
    return hours * 60.0 * 60.0


def s_to_h(seconds):
    return seconds / (60.0 * 60.0)
