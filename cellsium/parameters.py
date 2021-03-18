from tunable import Tunable


class RandomlyDistributed(Tunable):
    pass


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
