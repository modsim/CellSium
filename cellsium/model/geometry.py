"""Cell geometry model classes and routines."""
from math import cos, sin
from typing import Iterator, List, Tuple

import numpy as np

from ..geometry import (
    add_empty_third_dimension,
    circle_segment,
    line,
    parabolic_deformation,
    rotate,
    rotate3d,
    rotate_and_mesh,
    shift,
)
from ..typing import DefaultsType

CircleType = Tuple[float, Tuple[float, float]]


class Shape:
    """Base class for implementing cell shapes."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict()

    def raw_points(self, simplify: bool = False) -> np.ndarray:
        pass

    def get_approximation_circles(self) -> Iterator[CircleType]:
        pass


class Shape3D(Shape):
    """Base class for implementing 3D cell shapes."""

    def raw_points3d(self, steps: int = 32, simplify: bool = False) -> np.ndarray:
        pass


class RodShaped(Shape):
    """Rod shaped cell geometry."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(length=2.0, width=1.0)

    def rod_raw_points(
        self, simplify: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        diameter = self.width
        radius = diameter / 2.0
        length = self.length - diameter
        half_length = length / 2.0

        upper = line(
            [half_length, radius],
            [-half_length, radius],
            times=None if not simplify else 3,
        )
        lower = line(
            [-half_length, -radius],
            [half_length, -radius],
            times=None if not simplify else 3,
        )

        circle_left = circle_segment(radius, 90, 270, times=None if not simplify else 5)
        circle_left[:, 0] -= half_length

        circle_right = circle_segment(
            radius, -90, 90, times=None if not simplify else 5
        )
        circle_right[:, 0] += half_length

        return lower, circle_right, upper, circle_left

    def raw_points(self, simplify: bool = False) -> np.ndarray:
        lower, circle_right, upper, circle_left = self.rod_raw_points(simplify=simplify)
        return np.r_[lower, circle_right, upper, circle_left]

    def get_approximation_circles(self) -> Iterator[Tuple[float, Tuple[float, float]]]:
        diameter = self.width
        radius = diameter / 2.0
        length = self.length - diameter
        half_length = length / 2.0

        times = max(1, 2 * int(length / radius))

        for x in np.linspace(-half_length, half_length, times):
            yield radius, (x, 0)


class Rectangle(Shape):
    """Rectangular cell geometry."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(length=2.0, width=1.0)

    def raw_points(self, simplify: bool = False) -> DefaultsType:
        half_width, half_length = self.width / 2.0, self.length / 2.0

        return np.r_[
            line(
                [+half_length, +half_width],
                [-half_length, +half_width],
                times=None if not simplify else 3,
            ),
            line(
                [-half_length, +half_width],
                [-half_length, -half_width],
                times=None if not simplify else 3,
            ),
            line(
                [-half_length, -half_width],
                [+half_length, -half_width],
                times=None if not simplify else 3,
            ),
            line(
                [+half_length, -half_width],
                [+half_length, +half_width],
                times=None if not simplify else 3,
            ),
        ]

    def get_approximation_circles(self) -> Iterator[CircleType]:
        # not properly implemented
        diameter = self.width
        radius = diameter / 2.0
        length = self.length - diameter
        half_length = length / 2.0

        times = 2 * int(length / radius)

        for x in np.linspace(-half_length, half_length, times):
            yield radius, (x, 0)


class Square(Rectangle):
    """Square cell geometry."""

    def raw_points(self, simplify: bool = False) -> np.ndarray:
        # noinspection PyAttributeOutsideInit
        self.width = self.length
        return super().raw_points(simplify=simplify)


class BentRod(RodShaped):
    """Bent rod shaped cell geometry."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(bend_overall=0.0, bend_upper=0.0, bend_lower=0.0)

    def bend(self, points: np.ndarray) -> np.ndarray:
        u_idx, l_idx = points[:, 1] > 0, points[:, 1] < 0

        points[u_idx, :] = parabolic_deformation(points[u_idx, :], self.bend_upper)
        points[l_idx, :] = parabolic_deformation(points[l_idx, :], self.bend_lower)

        points = parabolic_deformation(points, self.bend_overall)

        return points

    def raw_points(self, simplify: bool = False) -> np.ndarray:
        lower, circle_right, upper, circle_left = self.rod_raw_points(simplify=simplify)

        points = np.r_[lower, circle_right, upper, circle_left]

        points = self.bend(points)

        return points

    def raw_points3d(
        self, steps: int = 16, simplify: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        lower, circle_right, upper, circle_left = self.rod_raw_points(simplify=simplify)
        points = np.r_[lower, circle_right, upper, circle_left]

        points, tris = rotate_and_mesh(add_empty_third_dimension(points), steps=steps)

        points = self.bend(points)

        return points, tris

    def get_approximation_circles(self) -> Iterator[CircleType]:
        radii = []
        offsets = []
        for radius, offset in super().get_approximation_circles():
            radii.append(radius)
            offsets.append(offset)
        offsets = np.array(offsets)
        offsets = parabolic_deformation(offsets, self.bend_overall)

        for radius, offset in zip(radii, offsets):
            yield radius, offset


class Coccoid(Shape):
    """Coccoid (spherical) cell geometry."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(length=1.0)

    def raw_points(self, simplify: bool = False) -> np.ndarray:
        radius = self.length / 2

        circle_left = circle_segment(radius, 90, 270, times=None if not simplify else 5)
        circle_right = circle_segment(
            radius, -90, 90, times=None if not simplify else 5
        )

        return np.r_[circle_right, circle_left]

    def get_approximation_circles(self) -> Iterator[CircleType]:
        yield self.length / 2, (0.0, 0.0)


class Ellipsoid(Coccoid):
    """Ellipsoid cell geometry."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(length=2.0, width=1.0)

    def raw_points(self, simplify: bool = False) -> np.ndarray:
        points = super().raw_points()

        a = self.length / 2
        b = self.width / 2

        points[:, 1] *= b / a

        return points


class WithPosition:
    """Mixin adding a cell position."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(position=lambda: [0.0, 0.0])


class WithAngle:
    """Mixin adding a cell angle."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(angle=0.0)


class WithFluorescence:
    """Mixin adding a fluorescence value."""

    @staticmethod
    def defaults() -> DefaultsType:
        return dict(fluorescences=lambda: [0.0])


class WithProperDivisionBehavior:
    """Mixin adding division angle calculation."""

    def get_division_positions(self, count: int = 2) -> List[List[float]]:
        # must have a length, a position and an angle

        sin_a, cos_a = sin(self.angle), cos(self.angle)

        x, y = self.position

        return [
            [float(x + factor * cos_a), float(y + factor * sin_a)]
            for factor in np.linspace(
                -self.length / 2 / 2, self.length / 2 / 2, num=count
            )
        ]


class AutoMesh3D(Shape3D):
    """Mixin adding automatic solid-of-revolution generation."""

    def points3d_on_canvas(
        self, steps: int = 16, simplify: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        points, triangles = self.raw_points3d(steps=steps, simplify=simplify)

        axis_vector = ((0,), (0,), (1,))

        position3d = self.position

        return shift(rotate3d(points, self.angle, axis_vector), position3d), triangles

    def raw_points3d(
        self, steps: int = 16, simplify: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        return rotate_and_mesh(
            add_empty_third_dimension(self.raw_points(simplify=simplify)), steps=steps
        )


class CellGeometry(WithAngle, WithPosition, AutoMesh3D):
    """Cell geometry base by combining multiple mixins."""

    def points_on_canvas(self) -> np.ndarray:
        return shift(rotate(self.raw_points(), self.angle), self.position)


__all__ = [
    'Shape',
    'Shape3D',
    'RodShaped',
    'Rectangle',
    'Square',
    'BentRod',
    'Coccoid',
    'Ellipsoid',
    'WithPosition',
    'WithAngle',
    'WithFluorescence',
    'WithProperDivisionBehavior',
    'AutoMesh3D',
    'CellGeometry',
]
