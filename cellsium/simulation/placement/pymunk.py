"""Placement simulation using Pymunk physics engine."""
import numpy as np
from tunable import Tunable

from ...model import PlacedCell
from .base import (
    PhysicalPlacement,
    PlacementSimulation,
    PlacementSimulationSimplification,
    ensure_python,
)

try:
    import pymunkoptions

    pymunkoptions.options['debug'] = False
except ImportError:
    pymunkoptions = None  # PyMunk 6.0.0 has removed pymunkoptions
# noinspection PyPep8
import pymunk


class ChipmunkPlacementRadius(Tunable):
    """Chipmunk placement radius, additional radius objects will have around them"""

    default: float = 0.05


class Chipmunk(PhysicalPlacement, PlacementSimulation, PlacementSimulation.Default):

    verbose: bool = False
    look_back_threshold: int = 5
    convergence_check_interval: int = 15

    def __init__(self):
        self.space = pymunk.Space(threaded=False)

        # self.space.threads = 2
        self.space.iterations = 100

        self.space.gravity = 0, 0

        self.boundary_bodies = []
        self.boundary_segments = []

        super().__init__()

    def add_boundary(self, coordinates: np.ndarray) -> None:
        coordinates = np.array(coordinates)

        boundary_body = pymunk.Body(body_type=pymunk.Body.STATIC)

        boundary_segments = []

        for start, stop in zip(coordinates, coordinates[1:]):
            self.boundaries.append([start, stop])
            segment = pymunk.Segment(
                boundary_body, ensure_python(start), ensure_python(stop), 0.0
            )
            boundary_segments.append(segment)

        self.space.add(boundary_body, *boundary_segments)

        self.boundary_bodies.append(boundary_body)
        self.boundary_segments.append(boundary_segments)

    def add(self, cell: PlacedCell) -> None:
        body = pymunk.Body(1.0, 1.0)
        body.position = pymunk.Vec2d(cell.position[0], cell.position[1])
        body.angle = cell.angle

        if PlacementSimulationSimplification.value == 2:
            shapes = tuple(
                pymunk.Circle(body, float(radius), offset=ensure_python(offset))
                for radius, offset in cell.get_approximation_circles()
            )
        else:
            points = cell.raw_points(
                simplify=PlacementSimulationSimplification.value == 1
            )

            poly = pymunk.Poly(body, ensure_python(points))
            poly.unsafe_set_radius(ChipmunkPlacementRadius.value)

            shapes = (poly,)

        self.cell_bodies[cell] = body
        self.cell_shapes[cell] = shapes

        self.space.add(body, *shapes)

    def remove(self, cell: PlacedCell) -> None:
        self.space.remove(self.cell_bodies[cell], *self.cell_shapes[cell])

        del self.cell_bodies[cell]
        del self.cell_shapes[cell]

    def clear(self) -> None:
        super().clear()

        for boundary_body, boundary_segments in zip(
            self.boundary_bodies, self.boundary_segments
        ):
            self.space.remove(boundary_body)
            self.space.remove(*boundary_segments)

        self.boundary_bodies.clear()
        self.boundary_segments.clear()

    def step(self, timestep: float) -> None:
        if len(self.cell_bodies) == 0:
            return

        resolution = 0.1 * 10
        times = timestep / resolution
        last = self.inner_step(
            time_step=resolution, iterations=int(times), epsilon=1e-12
        )
        _ = last

    def inner_step(
        self,
        time_step: float = 0.1,
        iterations: int = 9999,
        converge: bool = True,
        epsilon: float = 0.1,
    ) -> float:

        first_positions = self._get_positions()[:, :2]

        if converge:
            self._inner_step_step_attempt_converge(
                epsilon, first_positions, iterations, time_step
            )
        else:
            self._inner_step_step_ignore_converge(iterations, time_step)

        after_positions = self._get_positions()[:, :2]

        self._inner_step_update_positions()

        return self._total_distance(first_positions, after_positions)

    def _inner_step_update_positions(self) -> None:
        for cell, body in self.cell_bodies.items():
            cell.position = [body.position[0], body.position[1]]
            cell.angle = body.angle

    def _inner_step_step_ignore_converge(
        self, iterations: int, time_step: float
    ) -> None:
        for _ in range(iterations):
            self.space.step(time_step)

    def _inner_step_step_attempt_converge(
        self,
        epsilon: float,
        first_positions: np.ndarray,
        iterations: int,
        time_step: float,
    ) -> None:
        converging = False
        look_back = 0
        convergence_check = self.convergence_check_interval
        before_positions = first_positions.copy()
        for _ in range(iterations):
            self.space.step(time_step)

            convergence_check -= 1

            if convergence_check > 0:
                continue

            convergence_check = self.convergence_check_interval

            after_positions = self._get_positions()[:, :2]

            dist = (
                self._mean_distance(before_positions, after_positions)
                * time_step
                * self.convergence_check_interval
            )

            before_positions[:] = after_positions

            if dist < epsilon:
                look_back += 1
            else:
                look_back = 0

            if look_back > self.look_back_threshold:
                if self.verbose:
                    print("Stopping due to look back threshold.")
                break

            if self.verbose:
                print(_, dist, look_back)

            if not converging:
                if dist > 0:
                    converging = True
            else:
                if dist < epsilon:
                    break

            before_positions[:] = after_positions
