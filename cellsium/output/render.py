import cv2
import numpy as np

from . import Output
from ..random import RRF
from scipy.ndimage.interpolation import rotate
from scipy.interpolate import interp1d
from tunable import Tunable
from .. import Width, Height, Calibration, um_to_pixel, pixel_to_um


def noise_attempt(times=5, m=10, n=512, r=None):
    def make_rand(n, r):
        return interp1d(np.linspace(0, n, num=n), np.array([next(r) for _ in range(n)]), kind='cubic')

    def make_square(array):
        return np.tile(array, len(array)).reshape((len(array), len(array)))

    def make_it(n, m, r):
        return make_square(make_rand(m, r)(np.linspace(0, m, n)))

    two_n = 2*n

    the_sum = make_it(two_n, m, r)

    for _ in range(times):
        the_sum += rotate(make_it(two_n, m, r), angle=360.0*next(r), reshape=False)

    the_sum /= times

    the_sum = the_sum[n//2:two_n-n//2, n//2:two_n-n//2]
    return the_sum


def gaussian(array, dst=None, sigma=1.0):
    return cv2.GaussianBlur(array, (0, 0), sigmaX=um_to_pixel(sigma), dst=dst)


class LuminanceBackground(Tunable):
    default = 0.17


class LuminanceCell(Tunable):
    default = 0.07


def add_if_uneven(value, add=1):
    if (value % 2) == 0:
        return value
    else:
        return value + add


def new_canvas(dtype=np.float32):
    width, height = int(um_to_pixel(Width.value)), int(um_to_pixel(Height.value))
    # evenize
    width, height = add_if_uneven(width), add_if_uneven(height)
    canvas = np.zeros((height, width), dtype=dtype)
    return canvas


class PlainRenderer(Output):
    def __init__(self):
        super(PlainRenderer, self).__init__()

    def new_canvas(self):
        return new_canvas()

    def output(self, world):
        canvas = self.new_canvas()

        for cell in world.cells:
            points = um_to_pixel(cell.points_on_canvas())
            cv2.fillPoly(canvas, points[np.newaxis].astype(np.int32), 1.0)

        return canvas

    def convert(self, image):
        return (np.clip(image, 0, 1) * 255).astype(np.uint8)

    def write(self, world, file_name):
        cv2.imwrite(file_name, self.convert(self.output(world)))

    def display(self, world):
        cv2.imshow(self.__class__.__name__, self.convert(self.output(world)))
        cv2.waitKey()


class FluorescenceRenderer(PlainRenderer):
    def __init__(self):
        super(FluorescenceRenderer, self).__init__()

    def output(self, world):
        canvas = self.new_canvas()

        int_background = 1.0

        int_cell = 350.0 * int_background

        # for cell in self.cells:
        #     points = um_to_pixel(cell.points_on_canvas())
        #     cv2.fillPoly(canvas, points[np.newaxis].astype(np.int32), 1.0)

        emitter_size = (17, 17)

        emitter = np.zeros(emitter_size)
        emitter[emitter_size[0]//2, emitter_size[1]//2] = 1.0

        emitter = cv2.GaussianBlur(emitter, emitter_size, 2.5, 2.5)

        random_noise = RRF.new(np.random.normal, 0.0, 0.15, canvas.shape)

        canvas = next(random_noise)
        p_canvas = np.pad(canvas, emitter_size, mode='reflect')

        # this weird construction is necessary for a sequence of reproducible randomness
        class SeqOfPairsOfUniform(object):
            def set_bounds(self, x0, x1, y0, y1):
                self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1

            def next(self):
                return np.random.uniform(self.x0, self.x1), np.random.uniform(self.y0, self.y1)

        sopou = SeqOfPairsOfUniform()
        sopou_gen = RRF.new(sopou.next)

        heterogeneity = RRF.new(np.random.uniform, 0, 1)

        for cell in world.cells:
            points = um_to_pixel(cell.points_on_canvas())

            pts = points[np.newaxis].astype(np.int32)

            if next(heterogeneity) > 0.7:
                brightness = int_cell * 0.5
            else:
                brightness = int_cell

            int_countdown = brightness * (cv2.contourArea(pts) / 500.0)

            sopou.set_bounds(points[:, 0].min(), points[:, 0].max(), points[:, 1].min(), points[:, 1].max())

            while int_countdown > 0:
                x, y = next(sopou_gen)

                result = cv2.pointPolygonTest(pts, (x, y), measureDist=False)
                if result > 0.0:
                    p_canvas[int(y):int(y)+emitter_size[1], int(x):int(x)+emitter_size[0]] += emitter
                    int_countdown -= 1

        canvas = p_canvas[emitter_size[0]:-emitter_size[0], emitter_size[1]:-emitter_size[1]]

        gaussian(canvas, dst=canvas, sigma=0.025)

        return canvas


class PhaseContrastRenderer(PlainRenderer):
    def output(self, world):
        cell_canvas = super(PhaseContrastRenderer, self).output(world)

        canvas = LuminanceBackground.value * np.ones_like(cell_canvas)

        cell_mask = cell_canvas.copy()

        cell_canvas_black = gaussian(cell_canvas, sigma=0.75)

        #cell_canvas_black = cell_canvas_black - cell_canvas

        gaussian(cell_canvas, dst=cell_canvas, sigma=0.6)
        cell_canvas *= 0.9

        cell_canvas_black -= cell_canvas
        cell_canvas_black *= (1-cell_mask)

        # gaussian(canvas, dst=canvas, sigma=0.03)

        canvas = (1-cell_canvas) * canvas + LuminanceCell.value * cell_canvas

        canvas -= 0.50 * cell_canvas_black

        canvas += 0.5 * (1-cell_mask) * cell_canvas

        canvas -= 0.045*cell_mask

        gaussian(canvas, dst=canvas, sigma=0.05)

        return canvas


class UnevenIlluminationPhaseContrast(PhaseContrastRenderer):
    def __init__(self):
        super(UnevenIlluminationPhaseContrast, self).__init__()

        self.random_complex_noise = RRF.new(np.random.uniform, 0, 1)
        self.uneven_illumination = None
        self.create_uneven_illumination()

    def new_uneven_illumination(self):
        empty = self.new_canvas()
        return noise_attempt(
            times=5,
            m=10,
            n=max(empty.shape),
            r=self.random_complex_noise)[:empty.shape[0], :empty.shape[1]]

    def create_uneven_illumination(self):
        self.uneven_illumination = self.new_uneven_illumination()

    def output(self, world):
        canvas = super(UnevenIlluminationPhaseContrast, self).output(world)

        canvas = (canvas * (1.0 + 0.05 * complex_noise)) + 0.02 * complex_noise

        return canvas


class NoisyUnevenIlluminationPhaseContrast(PhaseContrastRenderer):
    def __init__(self):
        super(NoisyUnevenIlluminationPhaseContrast, self).__init__()

        empty = self.new_canvas()

        self.random_noise = RRF.new(np.random.normal, 0.0, 0.0175, empty.shape)

        self.product_noise = None
        self.sum_noise = None

    def new_noise(self):
        return next(self.random_noise)

    def create_noise(self):
        self.product_noise, self.sum_noise = self.new_noise()

    def output(self, world):
        canvas = super(NoisyUnevenIlluminationPhaseContrast, self).__init__(world)

        canvas = canvas * (1.0 + 0.05 * self.product_noise) + self.sum_noise * (1.0 + 0.05)

        return canvas
