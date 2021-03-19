import os
from pathlib import Path

import cv2
import numpy as np
from matplotlib import pyplot
from matplotlib.patches import PathPatch as MatplotlibPathPatch
from matplotlib.path import Path as MatplotlibPath
from roifile import ImagejRoi
from scipy.interpolate import interp1d
from scipy.ndimage.interpolation import rotate
from tifffile import TiffWriter
from tunable import Tunable

from ..model import WithFluorescence
from ..parameters import Height, Width, um_to_pixel
from ..random import RRF
from . import (
    Output,
    check_overwrite,
    ensure_path_and_extension,
    ensure_path_and_extension_and_number,
)
from .plot import MicrometerPerCm


def bytescale(image):
    if image.dtype == np.uint8:
        return image

    low, high = image.min(), image.max()
    return (255 * ((image - low) / (high - low))).astype(np.uint8)


def noise_attempt(times=5, m=10, n=512, r=None):
    # noinspection PyShadowingNames
    def make_rand(n, r):
        return interp1d(
            np.linspace(0, n, num=n),
            np.array([next(r) for _ in range(n)]),
            kind='cubic',
        )

    # noinspection PyShadowingNames
    def make_square(array):
        return np.tile(array, len(array)).reshape((len(array), len(array)))

    # noinspection PyShadowingNames
    def make_it(n, m, r):
        return make_square(make_rand(m, r)(np.linspace(0, m, n)))

    two_n = 2 * n

    the_sum = make_it(two_n, m, r)

    for _ in range(times):
        the_sum += rotate(make_it(two_n, m, r), angle=360.0 * next(r), reshape=False)

    the_sum /= times

    the_sum = the_sum[n // 2 : two_n - n // 2, n // 2 : two_n - n // 2]
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
    actions = [MatplotlibPath.MOVETO] + [MatplotlibPath.LINETO] * (len(coordinates) - 1)

    if 'closed' in kwargs:
        if kwargs['closed']:
            actions.append(MatplotlibPath.CLOSEPOLY)

            coordinates = np.r_[coordinates, [[0, 0]]]
        del kwargs['closed']

    patch = MatplotlibPathPatch(MatplotlibPath(coordinates, actions), **kwargs)
    return patch


def scale_points_relative(points, scale_points=1.0):
    if scale_points == 1.0:
        return points

    ma, mi = points.max(axis=0), points.min(axis=0)
    shift = mi + (ma - mi) * 0.5
    points = (scale_points * (points - shift)) + shift
    return points


def scale_points_absolute(points, delta=0.0):
    if delta == 0.0:
        return points

    ma, mi = points.max(axis=0), points.min(axis=0)
    shift = mi + (ma - mi) * 0.5
    scale_points = (ma - mi + delta) / (ma - mi)
    points = (scale_points * (points - shift)) + shift
    return points


# noinspection PyUnusedLocal
def render_on_canvas_cv2(canvas, array_of_points, scale_points=1.0, **kwargs):
    for points in array_of_points:
        points = scale_points_relative(points, scale_points)
        cv2.fillPoly(canvas, points[np.newaxis].astype(np.int32), 1.0)

    return canvas


def render_on_canvas_matplotlib(
    canvas, array_of_points, scale_points=1.0, over_sample=1
):
    interaction_state = pyplot.isinteractive()

    pyplot.ioff()

    dpi = 100.0
    fig = pyplot.figure(
        frameon=False,
        dpi=int(dpi),
        figsize=(
            over_sample * canvas.shape[1] / dpi,
            over_sample * canvas.shape[0] / dpi,
        ),
    )

    ax = fig.add_axes([0, 0, 1, 1])
    for points in array_of_points:
        points = scale_points_relative(points, scale_points)
        ax.add_patch(
            prepare_patch(
                points,
                edgecolor='black',
                facecolor='white',
                closed=True,
                linewidth=over_sample * 0.25,
            )
        )

    plt = ax.imshow(canvas, cmap='gray')

    ax.axis('off')

    plt.axes.get_xaxis().set_visible(False)
    plt.axes.get_yaxis().set_visible(False)

    fig.canvas.draw()

    canvas_data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(
        fig.canvas.get_width_height()[::-1] + (3,)
    )[:, :, 0]
    if canvas_data.max() > 0.0:
        canvas_data = canvas_data.astype(np.float32) / canvas_data.max()

    pyplot.close(fig.number)

    if over_sample != 1:
        cv2.resize(
            canvas_data,
            dst=canvas_data,
            dsize=canvas.shape[::-1],
            interpolation=cv2.INTER_AREA,
        )

    if interaction_state:
        pyplot.ion()

    return canvas_data


def get_canvas_points_raw(cell, image_height=None):
    points = um_to_pixel(cell.points_on_canvas())

    if image_height:
        # flip y, to have (0,0) bottom left
        points[:, 1] = image_height - points[:, 1]

    return points


def get_canvas_points_for_cell(cell, image_height=None):
    points = get_canvas_points_raw(cell, image_height=image_height)

    if RoiOutputScaleFactor.value != 1.0:
        points = scale_points_relative(points, scale_points=RoiOutputScaleFactor.value)
    if RoiOutputScaleDelta.value != 0.0:
        points = scale_points_absolute(points, delta=RoiOutputScaleDelta.value)

    return points


def cv2_has_write_support(extension):
    try:
        # Suppress a warning, apparently in some old JPEG2000 reading code there were security vulnerabilities
        # Since we only want to write here, it should be fine.
        os.environ['OPENCV_IO_ENABLE_JASPER'] = '1'
        return cv2.haveImageWriter(extension)
    except cv2.error:  # why does this function throw errors? just return True or False ...
        return False


OpenCV_Acceptable_Write_Extensions = [
    extension
    for extension in (
        '.bmp,.dib,.jpeg,.jpg,.jpe,.jp2,.png,.webp,.pbm,.pgm,'
        '.ppm,.pxm,.pnm,.pfm,.sr,.ras,.tiff,.tif,.exr,.hdr,.pic'
    ).split(',')
    if cv2_has_write_support(extension)
]

if '.png' in OpenCV_Acceptable_Write_Extensions:
    OpenCV_Acceptable_Write_Extensions.remove('.png')
    OpenCV_Acceptable_Write_Extensions = ['.png'] + OpenCV_Acceptable_Write_Extensions


class PlainRenderer(Output):

    write_debug_output = False

    def __init__(self):
        super().__init__()
        self.fig = self.ax = self.imshow_data = None

    @staticmethod
    def new_canvas():
        return new_canvas()

    @staticmethod
    def imwrite(name, img, overwrite=False, output_count=None):
        name = check_overwrite(
            ensure_path_and_extension_and_number(
                name,
                OpenCV_Acceptable_Write_Extensions,
                output_count,
                disable_individual=not output_count,
            ),
            overwrite=overwrite,
        )

        return cv2.imwrite(name, img)

    def debug_output(self, name, array):
        if not self.write_debug_output:
            return

        self.imwrite('render-%s.png' % (name,), bytescale(array), overwrite=True)

    @staticmethod
    def render_cells(canvas, array_of_points, fast=False):
        if fast:
            canvas = render_on_canvas_cv2(canvas, array_of_points)
        else:
            canvas = render_on_canvas_matplotlib(canvas, array_of_points)
        return canvas

    def output(self, world, **kwargs):
        canvas = self.new_canvas()

        array_of_points = [
            get_canvas_points_raw(cell, canvas.shape[0]) for cell in world.cells
        ]

        canvas = self.render_cells(canvas, array_of_points)

        self.debug_output('raw-cells', canvas)

        return canvas

    @staticmethod
    def convert(image, max_value=255):
        return (np.clip(image, 0, 1) * max_value).astype(np.uint8)

    def write(self, world, file_name, overwrite=False, output_count=0, **kwargs):
        self.imwrite(
            file_name,
            self.convert(self.output(world)),
            overwrite=overwrite,
            output_count=output_count,
        )

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
                    figsize=(
                        Width.value / MicrometerPerCm.value / 2.51,
                        Height.value / MicrometerPerCm.value / 2.51,
                    )
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
        super().__init__()
        canvas = self.new_canvas()

        self.rng = RRF.spawn_generator()

        self.random_noise = RRF.sequence.normal(
            FluorescenceNoiseMean.value,
            FluorescenceNoiseStd.value,
            canvas.shape,
        )

    def output(self, world, **kwargs):
        canvas = self.new_canvas()

        int_background = FluorescenceRatioBackground.value

        emitter_size = (
            FluorescenceEmitterKernelSizeW.value,
            FluorescenceEmitterKernelSizeH.value,
        )

        emitter = np.zeros(emitter_size)
        emitter[emitter_size[0] // 2, emitter_size[1] // 2] = 1.0

        emitter = cv2.GaussianBlur(
            emitter,
            emitter_size,
            sigmaX=FluorescenceEmitterGaussianW.value,
            sigmaY=FluorescenceEmitterGaussianH.value,
        )

        self.debug_output('fluorescence-emitter', emitter)

        p_canvas = np.pad(canvas, emitter_size, mode='reflect')

        for cell in world.cells:
            points = um_to_pixel(cell.points_on_canvas())
            #
            points[:, 1] = canvas.shape[0] - points[:, 1]

            pts = points[np.newaxis].astype(np.int32)

            # Skip cells which (partly) lie outside of the image
            # TODO proper handling, so that parts of cells poking into the image are still properly handled
            if (points[:, 0].min() < 0 or points[:, 0].max() > canvas.shape[1]) or (
                points[:, 1].min() < 0 or points[:, 1].max() > canvas.shape[0]
            ):
                continue

            if isinstance(cell, WithFluorescence):
                if self.channel < len(cell.fluorescences):
                    brightness = cell.fluorescences[self.channel] * int_background
                else:
                    brightness = 0

            else:
                brightness = 0

            # TODO normalize by µm^2
            int_countdown = brightness * (
                cv2.contourArea(pts) / FluorescenceCellSizeFactor.value
            )

            points_x_min, points_x_max = points[:, 0].min(), points[:, 0].max()
            points_y_min, points_y_max = points[:, 1].min(), points[:, 1].max()

            while int_countdown > 0:
                # TODO needs tests
                x = self.rng.uniform(points_x_min, points_x_max)
                y = self.rng.uniform(points_y_min, points_y_max)

                if cv2.pointPolygonTest(pts, (x, y), measureDist=False) > 0.0:
                    target = p_canvas[
                        int(y)
                        + emitter_size[1] // 2 : int(y)
                        + 3 * emitter_size[1] // 2,
                        int(x)
                        + emitter_size[0] // 2 : int(x)
                        + 3 * emitter_size[0] // 2,
                    ]
                    target += emitter[: target.shape[0], : target.shape[1]]
                    int_countdown -= 1

        canvas = p_canvas[
            emitter_size[0] : -emitter_size[0], emitter_size[1] : -emitter_size[1]
        ]

        self.debug_output('raw-fluorescence-cells', canvas)

        noise = int_background * np.abs(next(self.random_noise))

        self.debug_output('raw-fluorescence-noise', noise)

        canvas += noise

        self.debug_output('fluorescence', canvas)

        return canvas


class PhaseContrastRenderer(PlainRenderer):
    def output(self, world, **kwargs):
        cell_canvas = super().output(world)

        background = LuminanceBackground.value * np.ones_like(cell_canvas)

        self.debug_output('pc-background', background)

        cell_halo = 0.5 * gaussian(cell_canvas, sigma=0.75)

        background_w_halo = background + cell_halo

        self.debug_output('pc-halo-background', background_w_halo)

        cell_canvas = gaussian(cell_canvas, sigma=0.05)

        self.debug_output('pc-blurred-cells', cell_canvas)

        halo_glow_in_cells = (
            0.4
            * gaussian(cell_canvas, 0.1)
            * gaussian(cell_halo * (1 - cell_canvas), sigma=0.05)
        )

        self.debug_output('pc-blur-in-cells', halo_glow_in_cells)

        result = (
            background_w_halo * (1 - cell_canvas) + cell_canvas * LuminanceCell.value
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
        super().__init__()

        self.random_complex_noise = RRF.sequence.uniform(0, 1)
        self.uneven_illumination = None
        self.create_uneven_illumination()

    def new_uneven_illumination(self):
        empty = self.new_canvas()
        return noise_attempt(
            times=5, m=10, n=max(empty.shape), r=self.random_complex_noise
        )[: empty.shape[0], : empty.shape[1]]

    def create_uneven_illumination(self):
        self.uneven_illumination = self.new_uneven_illumination()

    def output(self, world, **kwargs):
        canvas = super().output(world)

        self.debug_output('uneven-illumination', self.uneven_illumination)

        canvas = (
            canvas
            * (
                1.0
                + UnevenIlluminationMultiplicativeFactor.value
                * self.uneven_illumination
            )
        ) + UnevenIlluminationAdditiveFactor.value * self.uneven_illumination

        self.debug_output('pc-with-uneven-illumination', canvas)

        return canvas


class NoisyUnevenIlluminationPhaseContrast(UnevenIlluminationPhaseContrast):
    def __init__(self):
        super().__init__()

        empty = self.new_canvas()

        self.product_noise = RRF.sequence.normal(1.0, 0.002, empty.shape)
        self.sum_noise = RRF.sequence.normal(0.0, 0.002, empty.shape)

    def output(self, world, **kwargs):
        canvas = super().output(world)

        product_noise = next(self.product_noise)
        sum_noise = next(self.sum_noise)

        self.debug_output('product_noise', product_noise)
        self.debug_output('sum_noise', sum_noise)

        canvas = canvas * product_noise + sum_noise

        self.debug_output('pc-uneven-w-noise', canvas)

        return canvas


class RoiOutputScaleFactor(Tunable):
    default = 1.0


class RoiOutputScaleDelta(Tunable):
    default = -4.0


def collect_subclasses(start):
    collector = set()

    def _recurse(class_):
        collector.add(class_)
        for subclass_ in class_.__subclasses__():
            _recurse(subclass_)

    _recurse(start)
    return collector


class RenderChannels(Tunable):
    default = 'NoisyUnevenIlluminationPhaseContrast'
    # default = 'NoisyUnevenIlluminationPhaseContrast, FluorescenceRenderer'

    @staticmethod
    def get_mapping():
        return {class_.__name__: class_ for class_ in collect_subclasses(PlainRenderer)}

    @classmethod
    def test(cls, value):
        mapping = cls.get_mapping()
        for class_ in value.split(','):
            if class_.strip() not in mapping:
                return False
        return True

    @classmethod
    def instantiate(cls):
        mapping = cls.get_mapping()
        return [mapping[class_.strip()]() for class_ in cls.value.split(',')]


class TiffOutput(Output):
    output_type = np.uint8

    def __init__(self):
        self.channels = RenderChannels.instantiate()
        self.images = []
        self.current = -1
        self.file_name = None
        self.rois = []

    def output(self, world, **kwargs):
        return [c.output(world) for c in self.channels]

    def __del__(self):
        if not self.images:
            return

        stack = []
        for stacklet in self.images:
            stacklet = np.concatenate([image[np.newaxis] for image in stacklet], axis=0)
            stack.append(stacklet[np.newaxis, np.newaxis])

        result = np.concatenate(stack)

        if self.output_type in (np.uint8, np.uint16):

            for c in range(result.shape[2]):
                result[:, 0, c, :, :] -= result[:, 0, c, :, :].min()
                result[:, 0, c, :, :] /= result[:, 0, c, :, :].max()

            result *= 2 ** (8 * np.dtype(self.output_type).itemsize) - 1

        result = result.astype(self.output_type)

        binary_rois = [ImagejRoi.frompoints(**roi).tobytes() for roi in self.rois]

        with TiffWriter(
            ensure_path_and_extension(self.file_name, '.tif'), imagej=True
        ) as writer:
            writer.save(
                result,
                resolution=(um_to_pixel(1.0), um_to_pixel(1.0)),
                metadata=dict(unit='um', Overlays=binary_rois),
            )

    def write(self, world, file_name, **kwargs):
        self.file_name = file_name

        self.current += 1

        stacklet = self.output(world)

        self.images.append(stacklet)

        for idx, cell in enumerate(world.cells):
            points = get_canvas_points_for_cell(cell, image_height=stacklet[0].shape[0])

            if len(self.channels) > 1:
                self.rois.append(
                    dict(points=points, t=self.current, position=-1, index=idx)
                )
            else:
                self.rois.append(
                    dict(points=points, t=-1, position=self.current, index=idx)
                )


__all__ = [
    'PlainRenderer',
    'FluorescenceRenderer',
    'PhaseContrastRenderer',
    'UnevenIlluminationPhaseContrast',
    'NoisyUnevenIlluminationPhaseContrast',
    'TiffOutput',
]
