"""Various geometry handling functions."""
from functools import lru_cache
from typing import Optional, Tuple

import numpy as np


@lru_cache(maxsize=128)
def cached_linspace(start: float, stop: float, num: int) -> np.ndarray:
    """
    A cached variant of np.linspace. Returns cached, no-write linspaces.

    :param start: Start
    :param stop: Stop
    :param num: Count of numbers to emit
    :return: Array
    """
    array = np.linspace(start=start, stop=stop, num=num)
    array.setflags(write=False)
    return array


def line(
    start: np.ndarray,
    stop: np.ndarray,
    interval: float = 0.1,
    minimum_times: int = 10,
    times: Optional[int] = None,
) -> np.ndarray:
    """
    Rasters a line from start to stop with points at interval interval.

    :param start: Start point
    :param stop: Stop point
    :param interval: Interval
    :param minimum_times: Minimal count of points to put between start and stop
    :param times: Alternatively: count of points to place
    :return: Coordinates
    """
    start, stop = np.atleast_2d(start), np.atleast_2d(stop)
    delta = stop - start

    if times is None:
        times = max(int(np.linalg.norm(delta) / interval) + 1, minimum_times)

    ramp = cached_linspace(start=0.0, stop=1.0, num=times)
    ramp = np.c_[ramp, ramp]

    return start + delta * ramp


def circle_segment(
    radius: float,
    start: np.ndarray,
    stop: np.ndarray,
    interval: float = 0.1,
    minimum_times: int = 10,
    times: Optional[int] = None,
) -> np.ndarray:
    """
    Rasters a circle segment from start to stop with a radius radius.

    :param radius: Radius
    :param start: Start point
    :param stop: Stop point
    :param interval: Interval
    :param minimum_times: Minimal count of points to put between start and stop
    :param times: Alternatively: count of points to place
    :return: Coordinates
    """
    interval = np.arctan(float(interval) / radius)
    start, stop = np.radians(start), np.radians(stop)

    if times is None:
        times = max(int((stop - start) / interval), minimum_times)
    ramp = cached_linspace(start, stop, times)
    return radius * np.c_[np.cos(ramp), np.sin(ramp)]


def parabolic_deformation(array: np.ndarray, factor: float) -> np.ndarray:
    """
    Deform array by a parabola.

    :param array: Coordinates
    :param factor: Factor
    :return: Deformed coordinates
    """
    array[:, 1] += factor * (array[:, 0] ** 2 - (array[:, 0] ** 2).max())
    return array


def get_rotation_matrix(angle: float) -> np.ndarray:
    """
    Creates a rotation matrix.

    :param angle: Angle
    :return: Rotation matrix
    """
    return np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])


def rotate(data: np.ndarray, angle: float) -> np.ndarray:
    """
    Rotates data by angle.

    :param data: Coordinates
    :param angle: Angle
    :return: Rotated coordinates
    """
    return np.dot(np.atleast_2d(data), get_rotation_matrix(angle).T)


def shift(data: np.ndarray, vector: np.ndarray) -> np.ndarray:
    """
    Shifts coordinates.

    :param data: Coordinates
    :param vector: Shift vector
    :return: Shifted coordinates
    """
    data = data.copy()
    vector = np.atleast_2d(vector)

    for n in range(min(data.shape[1], vector.shape[1])):
        data[:, n] += vector[0, n]

    return data


def add_empty_third_dimension(array: np.ndarray) -> np.ndarray:
    """
    Adds an empty third dimension.

    :param array: 2D Array
    :return: 3D Array
    """
    result = np.zeros((len(array), 3), dtype=array.dtype)
    result[:, :2] = array
    return result


def rotate3d(data: np.ndarray, angle: float, axis_vector: np.ndarray) -> np.ndarray:
    """
    Rotates data within 3D space around axis_vector.

    :param data: Coordinates
    :param angle: Angle
    :param axis_vector: Axis vector of the rotation
    :return: Rotated points
    """
    rotation_matrix = get_rotation_matrix3d_angle_axis(angle, axis_vector)
    return np.dot(np.atleast_2d(data), rotation_matrix.T)


def _cross_product_matrix(vec: np.ndarray) -> np.ndarray:
    """
    Helper function to prepare vec for usage within the rotation matrix function.

    :param vec: Input vector
    :return: Output vector
    """
    vec = np.atleast_2d(vec)[:, 0]

    return np.array([[0, -vec[2], vec[1]], [vec[2], 0, -vec[0]], [-vec[1], vec[0], 0]])


@lru_cache(maxsize=128)
def get_rotation_matrix3d_angle_axis(
    angle: float, axis_vector: np.ndarray
) -> np.ndarray:
    """
    Prepare a rotation matrix in 3D, caching the result.

    :param angle: Angle
    :param axis_vector: Axis to rotate around
    :return: Rotation matrix
    """
    cos_a, sin_a = np.cos(angle), np.sin(angle)

    r = (
        cos_a * np.eye(3)
        + sin_a * _cross_product_matrix(axis_vector)
        + (1 - cos_a) * np.tensordot(axis_vector, axis_vector, axes=0).reshape((3, 3))
    )

    r.setflags(write=False)

    return r


def rotate_and_mesh(
    points: np.ndarray, steps: int = 16, clean: bool = True, close_ends: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Produces a solid of revolution.

    :param points: Coordinates
    :param steps: Steps of the revolution
    :param clean: Whether to clean the data beforehand
    :param close_ends: Whether to close the ends
    :return: Tuple(Array of Points, Triangle Indices)
    """

    eps = np.finfo(points.dtype).eps

    # TODO: Check if clean can always be set and removed from params
    if clean:
        points = points[points[:, 1] > eps]

    if close_ends:
        points = np.r_[
            [[points[0, 0] + eps, 0, 0]], points, [[points[-1, 0] - eps, 0, 0]]
        ]

    all_points = points.repeat(steps, axis=0)

    axis_vector = (
        (1,),
        (0,),
        (0,),
    )
    max_angle = np.radians(360.0 if clean else 180.0)

    for n, (angle, idx) in enumerate(
        zip(
            cached_linspace(0, max_angle, num=steps),
            range(0, len(points) * steps, len(points)),
        )
    ):
        all_points[idx : idx + len(points)] = rotate3d(points, angle, axis_vector)

    # Triangle connectivity
    #
    # LAST 0 + n + 0 ---- 0 + n + 1 ----- 0 + n + 2
    #          |    \         |    \
    #          |      \       |      \
    #          |        \     |        \
    # BASE X + n + 0 ---- X + n + 1 ----- X + n + 2
    #

    triangles = []

    last = len(all_points) - len(points)

    for step in range(steps):
        base = step * len(points)
        for n in range(0, len(points) - 1):
            triangles.append(
                [
                    last + n + 0,
                    base + n + 1,
                    last + n + 1,
                ]
            )
            triangles.append([base + n + 0, base + n + 1, last + n])
        last = base

    return all_points, np.array(triangles)


__all__ = [
    'line',
    'circle_segment',
    'parabolic_deformation',
    'rotate',
    'shift',
    'add_empty_third_dimension',
    'rotate3d',
    'rotate_and_mesh',
]
