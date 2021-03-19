import json
from collections import namedtuple
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from tunable import Tunable

from . import Output, OutputReproducibleFiles
from .render import (
    PlainRenderer,
    RenderChannels,
    get_canvas_points_for_cell,
    new_canvas,
)

BBoxContour = namedtuple(
    'BBoxContour',
    [
        'points',
        'x_min',
        'x_max',
        'y_min',
        'y_max',
        'x_delta',
        'y_delta',
        'x_center',
        'y_center',
        'rel_x_delta',
        'rel_y_delta',
        'rel_x_center',
        'rel_y_center',
        'rel_x_min',
        'rel_x_max',
        'rel_y_min',
        'rel_y_max',
    ],
)


def get_bbox_for_cell(cell, shape):
    points = get_canvas_points_for_cell(cell, image_height=shape[0])

    x_min, x_max = points[:, 0].min(), points[:, 0].max()
    y_min, y_max = points[:, 1].min(), points[:, 1].max()

    x_delta, y_delta = (x_max - x_min), (y_max - y_min)
    x_center, y_center = x_min + x_delta / 2.0, y_min + y_delta / 2.0

    rel_x_delta, rel_y_delta = x_delta / shape[1], y_delta / shape[0]

    rel_x_center, rel_y_center = x_center / shape[1], y_center / shape[0]

    rel_x_max, rel_y_max = x_max / shape[1], y_max / shape[0]
    rel_x_min, rel_y_min = x_min / shape[1], y_min / shape[0]

    return BBoxContour(
        points=points,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        x_delta=x_delta,
        y_delta=y_delta,
        x_center=x_center,
        y_center=y_center,
        rel_x_delta=rel_x_delta,
        rel_y_delta=rel_y_delta,
        rel_x_center=rel_x_center,
        rel_y_center=rel_y_center,
        rel_x_min=rel_x_min,
        rel_x_max=rel_x_max,
        rel_y_min=rel_y_min,
        rel_y_max=rel_y_max,
    )


def is_completely_within(bbox):
    return (
        0 <= bbox.rel_x_min <= 1
        and 0 <= bbox.rel_x_max <= 1
        and bbox.rel_x_min < bbox.rel_x_max
    ) and (
        0 <= bbox.rel_y_min <= 1
        and 0 <= bbox.rel_y_max <= 1
        and bbox.rel_y_min < bbox.rel_y_max
    )


def remove_outside_cells(world, shape):
    world = world.copy()

    for cell in world.cells:
        if not is_completely_within(get_bbox_for_cell(cell, shape=shape)):
            world.remove(cell)

    world.commit()

    return world


def mkdirs(*args):
    for arg in args:
        if arg:
            arg.mkdir(parents=True, exist_ok=True)


class GroundTruthOnlyCompleteCells(Tunable):
    """ Whether to omit cells which would not be completely visible. """

    default = True


class GroundTruthOnlyCompleteCellsInImages(Tunable):
    """Whether to omit cells in rendered images which would not be completely visible,
    only active if GroundTruthOnlyCompleteCells is set as well."""

    default = True


class GroundTruthMaskCoordinateResolution(Tunable):
    """ Resolution for ground truth coordinate data (e.g. JSON files). """

    default = 0.1


class GroundTruthOutput(Output, Output.Virtual):
    def __init__(self):
        self.channels = RenderChannels.instantiate()
        assert len(self.channels) == 1

        self.canvas_shape = new_canvas().shape

        self.current = -1

        self.significant_digits = int(
            np.round(
                np.log(
                    (1 / GroundTruthMaskCoordinateResolution.value)
                    * max(self.canvas_shape)
                )
                / np.log(10)
            )
        )

    def output(self, world, **kwargs):
        raise RuntimeError("GroundTruthOutput s only support writing.")


class YOLOOutput(GroundTruthOutput):
    def write(self, world, file_name, overwrite=False, **kwargs):
        shape = self.canvas_shape
        digits = self.significant_digits

        self.current += 1

        base_path = Path(file_name)
        image_path = base_path  # / 'images'
        label_path = base_path  # / 'labels'

        if self.current == 0:
            # some initializations

            if not overwrite and base_path.exists():
                raise RuntimeError(f"Path {base_path} already exists. Not overwriting.")

            mkdirs(base_path, image_path, label_path)

            (base_path / 'classes.txt').write_text("cell\n")

        token = '%012d' % self.current

        image_file = image_path / (token + '.png')
        text_file = label_path / (token + '.txt')

        if (
            GroundTruthOnlyCompleteCells.value
            and GroundTruthOnlyCompleteCellsInImages.value
        ):
            world = remove_outside_cells(world, shape)

        for channel in self.channels:
            channel.write(world, str(image_file), overwrite=overwrite, output_count=-1)
            break  # only one channel supported

        lines = []

        for cell in world.cells:
            bbox = get_bbox_for_cell(cell, shape)

            if GroundTruthOnlyCompleteCells.value and not is_completely_within(bbox):
                continue

            class_ = 0  # only one class at the moment

            line = f'{class_} ' + ' '.join(
                ('%%.%df' % digits) % value
                for value in [
                    bbox.rel_x_center,
                    bbox.rel_y_center,
                    bbox.rel_x_delta,
                    bbox.rel_y_delta,
                ]
            )

            lines.append(line)

        text_file.write_text("\n".join(lines))


def binary_to_rle(mask):
    mask = mask.astype(bool).ravel(order='F')

    total = len(mask)

    delta = np.diff(mask)
    (lens,) = np.where(delta)
    lens[1:] -= lens[0:-1]

    lens[0] += 1  # we lost one with np.diff

    lens = np.r_[lens, [total - sum(lens)]]

    return lens


class COCOEncodeRLE(Tunable):
    """ Whether to encode segmentation data as RLE format. """

    default = False


class COCOOutputStuff(Tunable):
    """ Whether to output dense stuffthingmaps along the COCO data. """

    default = False


class COCOOutput(GroundTruthOutput):
    def __init__(self):
        super().__init__()

        self.annotation_file = None

        self.coco_structure = {
            'info': {
                'year': datetime.now().year,
                'version': '1.0',
                'description': "Dataset generated with CellSium",  # TODO: Add parameters?
                'contributor': "CellSium User",
                'url': 'https://github.com/modsim/cellsium',
                'date_created': self.now(),
            },
            'images': [],
            'annotations': [],
            'licenses': [
                {
                    'id': 0,
                    'name': "Public Domain Dedication",
                    'url': 'https://creativecommons.org/publicdomain/zero/1.0/',
                }
            ],
            'categories': [
                {
                    'id': 0,
                    'name': 'cell',
                    'supercategory': 'cell',
                }
            ],
        }

        self.annotation_file = None

    @staticmethod
    def now():
        if OutputReproducibleFiles.value:
            return '1970-01-01 00:00:00'
        else:
            return str(datetime.now()).split('.')[0]

    def __del__(self):
        if self.annotation_file:
            with self.annotation_file.open('w+') as fp:
                json.dump(self.coco_structure, fp, indent=' ' * 4)

    def write(self, world, file_name, overwrite=False, **kwargs):
        shape = self.canvas_shape
        digits = self.significant_digits
        write_stuff = COCOOutputStuff.value

        self.current += 1

        base_path = Path(file_name)
        image_path = base_path / 'train'

        stuff_path = None

        if COCOOutputStuff.value:
            stuff_path = base_path / 'stuffthings'

        if self.current == 0:
            # some initializations

            if not overwrite and base_path.exists():
                raise RuntimeError(f"Path {base_path} already exists. Not overwriting.")

            mkdirs(base_path, image_path, stuff_path)

            self.annotation_file = base_path / 'annotations.json'

        token = '%012d' % self.current

        image_file_name = token + '.png'

        image_file = image_path / image_file_name

        if (
            GroundTruthOnlyCompleteCells.value
            and GroundTruthOnlyCompleteCellsInImages.value
        ):
            world = remove_outside_cells(world, shape)

        for channel in self.channels:
            channel.write(world, str(image_file), overwrite=overwrite, output_count=-1)
            break  # only one channel supported

        self.coco_structure['images'].append(
            {
                'id': self.current,
                'width': self.canvas_shape[1],
                'height': self.canvas_shape[0],
                'file_name': image_file_name,
                'license': 0,
                'flickr_url': '',
                'coco_url': '',
                'date_captured': self.now(),
            }
        )

        class_ = 0 if not write_stuff else 1

        cells_coords = []

        for cell in world.cells:
            bbox = get_bbox_for_cell(cell, shape)

            if GroundTruthOnlyCompleteCells.value and not is_completely_within(bbox):
                continue

            if write_stuff:
                cells_coords.append(bbox.points)

            area = cv2.contourArea(bbox.points.astype(np.float32))

            if not COCOEncodeRLE.value:
                iscrowd = 0
                segmentation = [np.around(bbox.points.ravel(), digits).tolist()]
            else:
                iscrowd = 1

                mask = PlainRenderer.new_canvas()
                mask = PlainRenderer.render_cells(mask, [bbox.points], fast=True)
                mask = mask > 0.5

                lens = binary_to_rle(mask)

                segmentation = {'counts': lens.tolist(), 'size': shape}

            self.coco_structure['annotations'].append(
                {
                    'id': len(self.coco_structure['annotations']),
                    'image_id': self.current,
                    'category_id': class_,
                    'segmentation': segmentation,
                    'area': area,
                    'bbox': [bbox.x_min, bbox.y_min, bbox.x_delta, bbox.y_delta],
                    'iscrowd': iscrowd,
                }
            )

        if write_stuff:
            stuff_file = stuff_path / image_file_name

            GenericMaskOutput.imwrite(
                stuff_file,
                GenericMaskOutput.generate_cells_mask(
                    cells_coords, cell_value=class_, binary=True
                ),
                overwrite=overwrite,
            )


class MaskOutputBinary(Tunable):
    """Whether GenericMaskOutput masks should be binary or continuous"""

    value = True


class MaskOutputCellValue(Tunable):
    """Value for foreground in GenericMaskOutput masks"""

    value = 255


class GenericMaskOutput(GroundTruthOutput):
    @staticmethod
    def generate_cells_mask(cells, cell_value=1, binary=True):
        mask = PlainRenderer.new_canvas()

        mask = PlainRenderer.render_cells(mask, cells, fast=True)

        mask = PlainRenderer.convert(mask, max_value=cell_value)

        if binary:
            mask = np.digitize(mask, [0.5 * cell_value]).astype(np.uint8) * cell_value

        return mask

    @staticmethod
    def imwrite(*args, **kwargs):
        return PlainRenderer.imwrite(*args, **kwargs)

    def write(self, world, file_name, overwrite=False, **kwargs):
        shape = self.canvas_shape

        self.current += 1

        base_path = Path(file_name)
        image_path = base_path / 'images'
        mask_path = base_path / 'masks'

        if self.current == 0:
            # some initializations

            if not overwrite and base_path.exists():
                raise RuntimeError(f"Path {base_path} already exists. Not overwriting.")

            mkdirs(base_path, image_path, mask_path)

        token = '%012d' % self.current

        image_file = image_path / (token + '.png')
        mask_file = mask_path / (token + '.png')

        if (
            GroundTruthOnlyCompleteCells.value
            and GroundTruthOnlyCompleteCellsInImages.value
        ):
            world = remove_outside_cells(world, shape)

        for channel in self.channels:
            channel.write(world, str(image_file), overwrite=overwrite, output_count=-1)
            break  # only one channel supported

        cell_bboxes = [get_bbox_for_cell(cell, shape) for cell in world.cells]

        if GroundTruthOnlyCompleteCells.value:
            cell_bboxes = [
                cell_bbox
                for cell_bbox in cell_bboxes
                if is_completely_within(cell_bbox)
            ]

        mask = self.generate_cells_mask(
            [cell_bbox.points for cell_bbox in cell_bboxes],
            cell_value=MaskOutputCellValue.value,
            binary=MaskOutputBinary.value,
        )

        self.imwrite(mask_file, mask, overwrite=overwrite)


__all__ = [
    'YOLOOutput',
    'COCOOutput',
    'GenericMaskOutput',
]
