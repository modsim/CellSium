"""Main set of parameters for the simulation."""
from typing import Union

import numpy as np
from tunable import Tunable

NumericType = Union[float, np.ndarray]


class RandomlyDistributed(Tunable):
    """Parent class for randomly distributed tunables"""

    pass


class NewCellCount(Tunable):
    """New cells to add to the simulation"""

    default: int = 1


class NewCellRadiusFromCenter(RandomlyDistributed):
    """Maximum radius for new cells to be spawned from the origin"""

    default: float = 5.0


class NewCellWidthMean(RandomlyDistributed):
    """Mean cell width for new cells"""

    default: float = 1.0


class NewCellWidthStd(RandomlyDistributed):
    """Standard deviation of the width of new cells"""

    default: float = 0.1


class NewCellWidthAbsoluteMax(Tunable):
    """Absolute maximum width of new cells"""

    default: float = 1.5


class NewCellWidthAbsoluteMin(Tunable):
    """Absolute minimum width of new cells"""

    default: float = 0.75


class NewCellLength1Mean(RandomlyDistributed):
    """Mean cell length, subtype one"""

    default: float = 2.5


class NewCellLength1Std(RandomlyDistributed):
    """Standard deviation of the cell length, subtype one"""

    default: float = 0.15


class NewCellLength2Mean(RandomlyDistributed):
    """Mean cell length, subtype two"""

    default: float = 1.25


class NewCellLength2Std(RandomlyDistributed):
    """Standard deviation of the cell length, subtype one"""

    default: float = 0.15


class NewCellLengthAbsoluteMax(Tunable):
    """Absolute maximum length of new cells"""

    default: float = 3.5


class NewCellLengthAbsoluteMin(Tunable):
    """Absolute minimum length of new cells"""

    default: float = 0.8


class NewCellBendOverallLower(RandomlyDistributed):
    """Bend factor minimum for new new cells"""

    default: float = -0.1


class NewCellBendOverallUpper(RandomlyDistributed):
    """Bend factor maximum for new new cells"""

    default: float = 0.1


class NewCellBendUpperLower(RandomlyDistributed):
    """Bend factor minimum for the upper part of new new cells"""

    default: float = -0.1


class NewCellBendUpperUpper(RandomlyDistributed):
    """Bend factor maximum for the upper part of new new cells"""

    default: float = 0.1


class NewCellBendLowerLower(RandomlyDistributed):
    """Bend factor minimum for the lower part of new new cells"""

    default: float = -0.1


class NewCellBendLowerUpper(RandomlyDistributed):
    """Bend factor maximum for the lower part of new new cells"""

    default: float = 0.1


class Width(Tunable):
    """Width of the (outputted) simulation"""

    default: float = 40.0


class Height(Tunable):
    """Height of the (outputted) simulation"""

    default: float = 60.0


class Calibration(Tunable):
    """Calibration for outputs, micrometer per pixel"""

    default: float = 0.065


def pixel_to_um(pix: NumericType) -> NumericType:
    """
    Convert pixel to micrometer.

    :param pix: Pixel value
    :return: Micrometer value
    """
    return pix * Calibration.value


def um_to_pixel(um: NumericType) -> NumericType:
    """
    Convert micrometer to pixel.

    :param um: Micrometer value
    :return: Pixel value
    """
    return um / Calibration.value


def h_to_s(hours: NumericType) -> NumericType:
    """
    Convert hours to seconds.

    :param hours: Hours
    :return: Seconds
    """
    return hours * 60.0 * 60.0


def s_to_h(seconds: NumericType) -> NumericType:
    """
    Convert seconds to hours.

    :param seconds: Seconds
    :return: Hours
    """
    return seconds / (60.0 * 60.0)
