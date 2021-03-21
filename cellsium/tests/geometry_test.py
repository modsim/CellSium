import numpy as np
from numpy.testing import assert_array_almost_equal

from ..geometry import line
from ..model import Shape, Shape3D


def test_line():

    test_value = line([0, 0], [0, 2])
    desired_value = np.array(
        [
            [0.0, 0.0],
            [0.0, 0.1],
            [0.0, 0.2],
            [0.0, 0.3],
            [0.0, 0.4],
            [0.0, 0.5],
            [0.0, 0.6],
            [0.0, 0.7],
            [0.0, 0.8],
            [0.0, 0.9],
            [0.0, 1.0],
            [0.0, 1.1],
            [0.0, 1.2],
            [0.0, 1.3],
            [0.0, 1.4],
            [0.0, 1.5],
            [0.0, 1.6],
            [0.0, 1.7],
            [0.0, 1.8],
            [0.0, 1.9],
            [0.0, 2.0],
        ]
    )

    assert_array_almost_equal(test_value, desired_value)


def test_shape():
    s = Shape()
    s.raw_points()
    s.get_approximation_circles()


def test_shape3d():
    s = Shape3D()
    s.raw_points3d()
