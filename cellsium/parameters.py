from tunable import Tunable


class RandomlyDistributed(Tunable):
    """Parent class for randomly distributed tunables"""

    pass


class NewCellCount(Tunable):
    """New cells to add to the simulation"""

    default = 1


class NewCellRadiusFromCenter(RandomlyDistributed):
    """Maximum radius for new cells to be spawned from the origin"""

    default = 5.0


class NewCellWidthMean(RandomlyDistributed):
    """Mean cell width for new cells"""

    default = 1.0


class NewCellWidthStd(RandomlyDistributed):
    """Standard deviation of the width of new cells"""

    default = 0.1


class NewCellWidthAbsoluteMax(Tunable):
    """Absolute maximum width of new cells"""

    default = 1.5


class NewCellWidthAbsoluteMin(Tunable):
    """Absolute minimum width of new cells"""

    default = 0.75


class NewCellLength1Mean(RandomlyDistributed):
    """Mean cell length, subtype one"""

    default = 2.5


class NewCellLength1Std(RandomlyDistributed):
    """Standard deviation of the cell length, subtype one"""

    default = 0.15


class NewCellLength2Mean(RandomlyDistributed):
    """Mean cell length, subtype two"""

    default = 1.25


class NewCellLength2Std(RandomlyDistributed):
    """Standard deviation of the cell length, subtype one"""

    default = 0.15


class NewCellLengthAbsoluteMax(Tunable):
    """Absolute maximum length of new cells"""

    default = 3.5


class NewCellLengthAbsoluteMin(Tunable):
    """Absolute minimum length of new cells"""

    default = 0.8


class NewCellBendOverallLower(RandomlyDistributed):
    """Bend factor minimum for new new cells"""

    default = -0.1


class NewCellBendOverallUpper(RandomlyDistributed):
    """Bend factor maximum for new new cells"""

    default = 0.1


class NewCellBendUpperLower(RandomlyDistributed):
    """Bend factor minimum for the upper part of new new cells"""

    default = -0.1


class NewCellBendUpperUpper(RandomlyDistributed):
    """Bend factor maximum for the upper part of new new cells"""

    default = 0.1


class NewCellBendLowerLower(RandomlyDistributed):
    """Bend factor minimum for the lower part of new new cells"""

    default = -0.1


class NewCellBendLowerUpper(RandomlyDistributed):
    """Bend factor maximum for the lower part of new new cells"""

    default = 0.1


class Width(Tunable):
    """Width of the (outputed) simulation"""

    default = 40.0


class Height(Tunable):
    """Height of the (outputed) simulation"""

    default = 60.0


class Calibration(Tunable):
    """Calibration for outputs, micrometer per pixel"""

    default = 0.065


def pixel_to_um(pix):
    """
    Convert pixel to micrometer.

    :param pix: Pixel value
    :return: Micrometer value
    """
    return pix * Calibration.value


def um_to_pixel(um):
    """
    Convert micrometer to pixel.

    :param um: Micrometer value
    :return: Pixel value
    """
    return um / Calibration.value


def h_to_s(hours):
    """
    Convert hours to seconds.

    :param hours: Hours
    :return: Seconds
    """
    return hours * 60.0 * 60.0


def s_to_h(seconds):
    """
    Convert seconds to hours.

    :param seconds: Seconds
    :return: Hours
    """
    return seconds / (60.0 * 60.0)
