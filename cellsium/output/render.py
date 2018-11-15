import cv2
import numpy as np

from matplotlib import pyplot
from imagej_tiff_meta import TiffWriter
from matplotlib.path import Path
from matplotlib.patches import PathPatch


from . import Output
from ..random import RRF, enforce_bounds
from scipy.misc import bytescale
from scipy.ndimage.interpolation import rotate
from scipy.interpolate import interp1d
from tunable import Tunable
from ..parameters import Width, Height, Calibration, pixel_to_um, um_to_pixel

from .plot import MicrometerPerCm

from ..model import WithFluorescence


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
    default = 0.075


def add_if_uneven(value, add=1):
    if (value % 2) == 0:
        return value
    else:
        return value + add


def new_canvas(dtype=np.float32):
    width, height = int(um_to_pixel(Width.value)), int(um_to_pixel(Height.value))
    # make even
    width, height = add_if_uneven(width), add_if_uneven(height)
    canvas = np.zeros((height, width), dtype=dtype)
    return canvas


class OpenCVimshow(Tunable):
    default = False


def prepare_patch(coordinates, **kwargs):
    actions = [Path.MOVETO] + [Path.LINETO] * (len(coordinates) - 1)

    if 'closed' in kwargs:
        if kwargs['closed']:
            actions.append(Path.CLOSEPOLY)

            coordinates = np.r_[coordinates, [[0, 0]]]
        del kwargs['closed']

    patch = PathPatch(Path(coordinates, actions), **kwargs)
    return patch


def scale_points_relative(points, scale_points=1.0):
    if scale_points == 1.0:
        return points

    ma, mi = points.max(axis=0), points.min(axis=0)
    shift = mi - (ma - mi) * 0.5
    points = (scale_points * (points - shift)) + shift
    return points


def render_on_canvas_cv2(canvas, array_of_points, scale_points=1.0):
    for points in array_of_points:
        points = scale_points_relative(points, scale_points)
        cv2.fillPoly(canvas, points[np.newaxis].astype(np.int32), 1.0)

    return canvas


def render_on_canvas_matplotlib(canvas, array_of_points, scale_points=1.0, over_sample=1):
    interaction_state = pyplot.isinteractive()

    pyplot.ioff()

    dpi = 100.0
    fig = pyplot.figure(frameon=False, dpi=int(dpi), figsize=(over_sample * canvas.shape[1] / dpi, over_sample * canvas.shape[0] / dpi))

    ax = fig.add_axes([0, 0, 1, 1])
    for points in array_of_points:
        points = scale_points_relative(points, scale_points)
        ax.add_patch(prepare_patch(points, edgecolor='black', facecolor='white', closed=True, linewidth=over_sample * 0.25))

    plt = ax.imshow(canvas, cmap='gray')

    ax.axis('off')

    plt.axes.get_xaxis().set_visible(False)
    plt.axes.get_yaxis().set_visible(False)

    fig.canvas.draw()

    canvas_data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(
        fig.canvas.get_width_height()[::-1] + (3,))[:, :, 0]
    if canvas_data.max() > 0.0:
        canvas_data = canvas_data.astype(np.float32) / canvas_data.max()

    pyplot.close(fig.number)

    if over_sample != 1:
        cv2.resize(canvas_data, dst=canvas_data, dsize=canvas.shape[::-1], interpolation=cv2.INTER_AREA)

    if interaction_state:
        pyplot.ion()

    return canvas_data


class PlainRenderer(Output):

    write_debug_output = False

    def __init__(self):
        super(PlainRenderer, self).__init__()
        self.fig = self.ax = self.imshow_data = None

    @staticmethod
    def new_canvas():
        return new_canvas()

    def debug_output(self, name, array):
        if not self.write_debug_output:
            return

        cv2.imwrite('render-%s.png' % (name,), bytescale(array))

    def output(self, world, **kwargs):
        canvas = self.new_canvas()

        array_of_points = []

        for cell in world.cells:
            points = um_to_pixel(cell.points_on_canvas())
            # flip y, to have (0,0) bottom left
            points[:, 1] = canvas.shape[0] - points[:, 1]

            array_of_points.append(points)

        # canvas = render_on_canvas_cv2(canvas, array_of_points)
        canvas = render_on_canvas_matplotlib(canvas, array_of_points)

        self.debug_output('raw-cells', canvas)

        return canvas

    @staticmethod
    def convert(image):
        return (np.clip(image, 0, 1) * 255).astype(np.uint8)

    def write(self, world, file_name, **kwargs):
        cv2.imwrite(file_name, self.convert(self.output(world)))

    def display(self, world, **kwargs):

        image = self.output(world)

        if OpenCVimshow.value:
            cv2.imshow(self.__class__.__name__, self.convert(image))
            cv2.waitKey()
        else:
            from matplotlib import pyplot

            pyplot.ion()

            if getattr(self, 'fig', None) is None:
                self.fig = pyplot.figure(
                    figsize=(Width.value / MicrometerPerCm.value / 2.51, Height.value / MicrometerPerCm.value / 2.51)
                )

            if getattr(self, 'ax', None) is None:
                self.ax = self.fig.add_subplot(111)

            if getattr(self, 'imshow_data', None):
                self.imshow_data.set_data(image)
            else:
                self.ax.clear()
                self.imshow_data = self.ax.imshow(image, cmap='gray')

                pyplot.tight_layout()
                pyplot.show()

            self.fig.canvas.draw()
            self.fig.canvas.flush_events()


# this weird construction is necessary for a sequence of reproducible randomness
class SeqOfPairsOfUniform(object):
    __slots__ = 'x0', 'x1', 'y0', 'y1'

    def __init__(self):
        self.x0, self.x1, self.y0, self.y1 = 0, 0, 0, 0

    def set_bounds(self, x0, x1, y0, y1):
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1

    def next(self):
        return np.random.uniform(self.x0, self.x1), np.random.uniform(self.y0, self.y1)


class FluorescenceEmitterKernelSizeW(Tunable):
    default = 17


class FluorescenceEmitterKernelSizeH(Tunable):
    default = 17


class FluorescenceEmitterGaussianW(Tunable):
    default = 2.5


class FluorescenceEmitterGaussianH(Tunable):
    default = 2.5


class FluorescenceNoiseMean(Tunable):
    default = 0.0


class FluorescenceNoiseStd(Tunable):
    default = 0.15


class FluorescenceRatioBackground(Tunable):
    default = 1.0


class FluorescenceCellSizeFactor(Tunable):
    default = 500.0


class FluorescenceRenderer(PlainRenderer):

    channel = 0

    def __init__(self):
        super(FluorescenceRenderer, self).__init__()
        canvas = self.new_canvas()

        self.random_noise = RRF.new(np.random.normal, FluorescenceNoiseMean.value, FluorescenceNoiseStd.value, canvas.shape)

    def output(self, world, **kwargs):
        canvas = self.new_canvas()

        int_background = FluorescenceRatioBackground.value

        emitter_size = (FluorescenceEmitterKernelSizeW.value, FluorescenceEmitterKernelSizeH.value)

        emitter = np.zeros(emitter_size)
        emitter[emitter_size[0]//2, emitter_size[1]//2] = 1.0

        emitter = cv2.GaussianBlur(emitter, emitter_size,
                                   sigmaX=FluorescenceEmitterGaussianW.value,
                                   sigmaY=FluorescenceEmitterGaussianH.value)

        self.debug_output('fluorescence-emitter', emitter)

        p_canvas = np.pad(canvas, emitter_size, mode='reflect')

        sopou = SeqOfPairsOfUniform()
        sopou_gen = RRF.new(sopou.next)

        for cell in world.cells:
            points = um_to_pixel(cell.points_on_canvas())
            #
            points[:, 1] = canvas.shape[0] - points[:, 1]

            pts = points[np.newaxis].astype(np.int32)

            # Skip cells which (partly) lie outside of the image
            # TODO proper handling, so that parts of cells poking into the image are still properly handled
            if ((points[:, 0].min() < 0 or points[:, 0].max() > canvas.shape[1]) or
                    (points[:, 1].min() < 0 or points[:, 1].max() > canvas.shape[0])):
                continue

            if isinstance(cell, WithFluorescence):
                if self.channel < len(cell.fluorescences):
                    brightness = cell.fluorescences[self.channel] * int_background
                else:
                    brightness = 0

            else:
                brightness = 0

            # TODO normalize by µm^2
            int_countdown = brightness * (cv2.contourArea(pts) / FluorescenceCellSizeFactor.value)

            sopou.set_bounds(points[:, 0].min(), points[:, 0].max(), points[:, 1].min(), points[:, 1].max())

            while int_countdown > 0:
                x, y = next(sopou_gen)

                if cv2.pointPolygonTest(pts, (x, y), measureDist=False) > 0.0:
                    target = p_canvas[
                             int(y)+emitter_size[1]//2:int(y)+3*emitter_size[1]//2,
                             int(x)+emitter_size[0]//2:int(x)+3*emitter_size[0]//2
                             ]
                    target += emitter[:target.shape[0], :target.shape[1]]
                    int_countdown -= 1

        canvas = p_canvas[emitter_size[0]:-emitter_size[0], emitter_size[1]:-emitter_size[1]]

        self.debug_output('raw-fluorescence-cells', canvas)

        noise = int_background * np.abs(next(self.random_noise))

        self.debug_output('raw-fluorescence-noise', noise)

        canvas += noise

        self.debug_output('fluorescence', canvas)

        return canvas


class PhaseContrastRenderer(PlainRenderer):
    def output(self, world, **kwargs):
        cell_canvas = super(PhaseContrastRenderer, self).output(world)

        background = LuminanceBackground.value * np.ones_like(cell_canvas)

        self.debug_output('pc-background', background)

        cell_halo = 0.5 * gaussian(cell_canvas, sigma=0.75)

        background_w_halo = background + cell_halo

        self.debug_output('pc-halo-background', background_w_halo)

        cell_canvas = gaussian(cell_canvas, sigma=0.05)

        self.debug_output('pc-blurred-cells', cell_canvas)

        halo_glow_in_cells = 0.4 * gaussian(cell_canvas, 0.1) * gaussian(cell_halo * (1 - cell_canvas), sigma=0.05)

        self.debug_output('pc-blur-in-cells', halo_glow_in_cells)

        result = (
            background_w_halo * (1 - cell_canvas)
            + cell_canvas * LuminanceCell.value
        ) + halo_glow_in_cells

        self.debug_output('pc-unblurred-result', result)

        result = gaussian(result, dst=result, sigma=0.075)

        self.debug_output('pc-result', result)

        return result


class UnevenIlluminationAdditiveFactor(Tunable):
    default = 0.02


class UnevenIlluminationMultiplicativeFactor(Tunable):
    # default = 0.05
    default = 0.25


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

    def output(self, world, **kwargs):
        canvas = super(UnevenIlluminationPhaseContrast, self).output(world)

        self.debug_output('uneven-illumination', self.uneven_illumination)

        canvas = (
            (canvas * (1.0 + UnevenIlluminationMultiplicativeFactor.value * self.uneven_illumination))
            + UnevenIlluminationAdditiveFactor.value * self.uneven_illumination
        )

        self.debug_output('pc-with-uneven-illumination', canvas)

        return canvas


class NoisyUnevenIlluminationPhaseContrast(UnevenIlluminationPhaseContrast):
    def __init__(self):
        super(NoisyUnevenIlluminationPhaseContrast, self).__init__()

        empty = self.new_canvas()

        self.product_noise = RRF.new(np.random.normal, 1.0, 0.002, empty.shape)
        self.sum_noise = RRF.new(np.random.normal, 0.0, 0.002, empty.shape)

    def output(self, world, **kwargs):
        canvas = super(NoisyUnevenIlluminationPhaseContrast, self).output(world)

        product_noise = next(self.product_noise)
        sum_noise = next(self.sum_noise)

        self.debug_output('product_noise', product_noise)
        self.debug_output('sum_noise', sum_noise)

        canvas = canvas * product_noise + sum_noise

        self.debug_output('pc-uneven-w-noise', canvas)

        return canvas


class TiffOutput(Output):

    channels = [NoisyUnevenIlluminationPhaseContrast, FluorescenceRenderer]
    channels = [NoisyUnevenIlluminationPhaseContrast] # , FluorescenceRenderer]
    output_type = np.uint8

    def __init__(self):
        self.channels = [c() for c in self.channels]
        self.images = []
        self.current = -1
        self.writer = None

    def output(self, world, **kwargs):
        return [c.output(world) for c in self.channels]

    def __del__(self):
        stack = []
        for stacklet in self.images:
            stacklet = np.concatenate([image[np.newaxis] for image in stacklet], axis=0)
            stack.append(stacklet[np.newaxis, np.newaxis])

        result = np.concatenate(stack)

        if self.output_type in (np.uint8, np.uint16):

            for c in range(result.shape[2]):
                result[:, 0, c, :, :] -= result[:, 0, c, :, :].min()
                result[:, 0, c, :, :] /= result[:, 0, c, :, :].max()

            result *= 2**(8*np.dtype(self.output_type).itemsize) - 1

        result = result.astype(self.output_type)

        self.writer.save(result)

    def write(self, world, file_name, **kwargs):
        if not file_name.endswith('.tif'):
            file_name += '.tif'
        if self.writer is None:
            self.writer = TiffWriter(file_name)

        self.current += 1

        stacklet = self.output(world)

        self.images.append(stacklet)

        for cell in world.cells:
            points = um_to_pixel(cell.points_on_canvas())
            # flip y, to have (0,0) bottom left
            canvas = stacklet[0]
            points[:, 1] = canvas.shape[0] - points[:, 1]

            for c, _ in enumerate(self.channels):
                self.writer.add_roi(points, c=c, z=0, t=self.current)
