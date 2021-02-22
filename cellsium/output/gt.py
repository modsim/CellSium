import json
from collections import namedtuple
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from tunable import Tunable

from . import Output
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
    )


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
        raise NotImplementedError()


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

            base_path.mkdir(parents=True, exist_ok=True)

            (base_path / 'classes.txt').write_text("cell\n")

            image_path.mkdir(parents=True, exist_ok=True)
            label_path.mkdir(parents=True, exist_ok=True)

        token = '%012d' % self.current

        image_file = image_path / (token + '.png')
        text_file = label_path / (token + '.txt')

        for channel in self.channels:
            channel.write(world, str(image_file))
            break  # only one channel supported

        lines = []

        for cell in world.cells:
            bbox = get_bbox_for_cell(cell, shape)

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


class COCOOutput(GroundTruthOutput):
    def __init__(self):
        super().__init__()

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
        return str(datetime.now()).split('.')[0]

    def __del__(self):
        if self.annotation_file:
            with self.annotation_file.open('w+') as fp:
                json.dump(self.coco_structure, fp, indent=' ' * 4)

    def write(self, world, file_name, overwrite=False, **kwargs):
        shape = self.canvas_shape
        digits = self.significant_digits
        self.current += 1

        base_path = Path(file_name)
        image_path = base_path

        if self.current == 0:
            # some initializations

            if not overwrite and base_path.exists():
                raise RuntimeError(f"Path {base_path} already exists. Not overwriting.")

            base_path.mkdir(parents=True, exist_ok=True)
            image_path.mkdir(parents=True, exist_ok=True)

            self.annotation_file = base_path / 'annotations.json'

        token = '%012d' % self.current

        image_file_name = token + '.png'

        image_file = image_path / image_file_name

        for channel in self.channels:
            channel.write(world, str(image_file))
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

        class_ = 0

        for cell in world.cells:
            bbox = get_bbox_for_cell(cell, shape)

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


class MaskOutputBinary(Tunable):
    """Whether GenericMaskOutput masks should be binary or continuous"""

    value = True


class MaskOutputCellValue(Tunable):
    """Value for foreground in GenericMaskOutput masks"""

    value = 255


class GenericMaskOutput(GroundTruthOutput):
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

            base_path.mkdir(parents=True, exist_ok=True)

            image_path.mkdir(parents=True, exist_ok=True)
            mask_path.mkdir(parents=True, exist_ok=True)

        token = '%012d' % self.current

        image_file = image_path / (token + '.png')
        mask_file = mask_path / (token + '.png')

        for channel in self.channels:
            channel.write(world, str(image_file))
            break  # only one channel supported

        mask = PlainRenderer.new_canvas()

        cells = [get_bbox_for_cell(cell, shape).points for cell in world.cells]

        mask = PlainRenderer.render_cells(mask, cells, fast=True)

        max_value = MaskOutputCellValue.value

        mask = PlainRenderer.convert(mask, max_value=max_value)

        if MaskOutputBinary.value:
            mask = np.digitize(mask, [0.5 * max_value]).astype(np.uint8) * max_value

        PlainRenderer.imwrite(mask_file, mask)
