from functools import lru_cache

import numpy as np


@lru_cache(maxsize=128)
def cached_linspace(start, stop, num):
    array = np.linspace(start=start, stop=stop, num=num)
    array.setflags(write=False)
    return array


def line(start, stop, interval=0.1, minimum_times=10, times=None):
    start, stop = np.atleast_2d(start), np.atleast_2d(stop)
    delta = stop - start

    if times is None:
        times = max(int(np.linalg.norm(delta) / interval) + 1, minimum_times)

    ramp = cached_linspace(start=0.0, stop=1.0, num=times)
    ramp = np.c_[ramp, ramp]

    return start + delta * ramp


def circle_segment(radius, start, stop, interval=0.1, minimum_times=10, times=None):
    interval = np.arctan(float(interval) / radius)
    start, stop = np.radians(start), np.radians(stop)

    if times is None:
        times = max(int((stop - start) / interval), minimum_times)
    ramp = cached_linspace(start, stop, times)
    return radius * np.c_[np.cos(ramp), np.sin(ramp)]


def parabolic_deformation(array, factor):
    array[:, 1] += factor * (array[:, 0] ** 2 - (array[:, 0] ** 2).max())
    return array


def get_rotation_matrix(angle):
    return np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])


def rotate(data, angle):
    return np.dot(np.atleast_2d(data), get_rotation_matrix(angle).T)


def shift(data, vector):
    data = data.copy()
    vector = np.atleast_2d(vector)

    for n in range(min(data.shape[1], vector.shape[1])):
        data[:, n] += vector[0, n]

    return data


def add_empty_third_dimension(array):
    result = np.zeros((len(array), 3), dtype=array.dtype)
    result[:, :2] = array
    return result


def rotate3d(data, angle, axis_vector):
    rotation_matrix = get_rotation_matrix3d_angle_axis(angle, axis_vector)
    return np.dot(np.atleast_2d(data), rotation_matrix.T)


def cross_product_matrix(vec):
    vec = np.atleast_2d(vec)[:, 0]

    return np.array([[0, -vec[2], vec[1]], [vec[2], 0, -vec[0]], [-vec[1], vec[0], 0]])


@lru_cache(maxsize=128)
def get_rotation_matrix3d_angle_axis(angle, axis_vector):
    cos_a, sin_a = np.cos(angle), np.sin(angle)

    r = (
        cos_a * np.eye(3)
        + sin_a * cross_product_matrix(axis_vector)
        + (1 - cos_a) * np.tensordot(axis_vector, axis_vector, axes=0).reshape((3, 3))
    )

    r.setflags(write=False)

    return r


def rotate_and_mesh(points, steps=16, clean=True, close_ends=True):
    """
    Produces a solid of revolution.

    :param points:
    :param steps:
    :param clean:
    :param close_ends:
    :return:
    """

    eps = np.finfo(points.dtype).eps

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
