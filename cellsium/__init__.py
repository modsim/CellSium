
__version__ = '0.0.1'

__author__ = 'Christian C. Sachs'

__citation__ = ''

__banner__ = ''

from tunable import Tunable


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
