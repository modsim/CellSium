"""Helper script to prepare real data for ML comparison study
 with CellSium's COCO/YOLO format writers"""
# pylint: disable=missing-class-docstring,missing-function-docstring
import sys
from typing import Dict, Iterator, List, Tuple, Iterable

import cv2
import numpy as np
import tifffile
import roifile

from cellsium.parameters import Calibration, Width, Height
from cellsium.simulation.simulator import World
from cellsium.output.all import COCOOutput, YOLOOutput
from cellsium.output.gt import GroundTruthOnlyCompleteCells

GroundTruthOnlyCompleteCells.value = False


class MockCellGeometry:  # pylint: disable=too-few-public-methods
    def __init__(self, coordinates: np.ndarray, shape: Tuple[int, int]):
        self.coordinates = coordinates
        self.shape = shape

    def points_on_canvas(self) -> np.ndarray:
        image_height = self.shape[0]
        points = self.coordinates.copy()
        points[:, 1] = image_height - points[:, 1]
        return points


def get_overlays(
    binary_overlays: Iterable[bytes], attribute: str = 'position'
) -> Dict[int, roifile.ImagejRoi]:
    raw_overlays = [
        roifile.ImagejRoi.frombytes(binary_overlay)
        for binary_overlay in binary_overlays
    ]
    overlays = {}
    for overlay in raw_overlays:
        num = getattr(overlay, attribute)
        if num not in overlays:
            overlays[num] = []
        overlays[num].append(overlay)
    return overlays


def get_tiff_frames_overlays(
    file_name: str,
) -> Iterator[Tuple[np.ndarray, List[roifile.ImagejRoi]]]:
    with tifffile.TiffFile(file_name) as tiff:
        overlays = get_overlays(
            tiff.imagej_metadata['Overlays']  # pylint: disable=unsubscriptable-object
        )

        for i, page in enumerate(tiff.pages):
            yield page.asarray(), overlays[i + 1]


def _write_channels(
    world: World,
    filenames: Iterable[str],
    overwrite: bool = True,  # pylint: disable=unused-argument
) -> None:
    cv2.imwrite(str(filenames[0]), world.__dict__['frame'])  # pylint: disable=no-member


def main():
    file_name, output_name = sys.argv[1], sys.argv[2]

    outputs = []

    Calibration.value = 1.0
    for frame, overlays in get_tiff_frames_overlays(file_name):
        Height.value, Width.value = frame.shape[0], frame.shape[1]

        if not outputs:
            for output in [COCOOutput(), YOLOOutput()]:
                output._write_channels = (  # pylint: disable=protected-access
                    _write_channels
                )
                outputs.append(output)

        world = World()
        world.__dict__['frame'] = frame

        for overlay in overlays:
            world.add(MockCellGeometry(overlay.coordinates().astype(float), shape=frame.shape))

        world.commit()

        for output in outputs:
            if isinstance(output, YOLOOutput):
                output.write(world, output_name + '/train', overwrite=True)
            else:
                output.write(world, output_name, overwrite=True)


if __name__ == '__main__':
    main()
