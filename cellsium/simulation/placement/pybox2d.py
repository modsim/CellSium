# noinspection PyPep8Naming
import Box2D as B2D
import numpy as np

from .base import (
    PhysicalPlacement,
    PlacementSimulation,
    PlacementSimulationSimplification,
    ensure_python,
)


class Box2D(PhysicalPlacement, PlacementSimulation):

    verbose = False

    def __init__(self):
        self.world = B2D.b2World()
        self.world.gravity = 0, 0

        super().__init__()

    def add_boundary(self, coordinates):
        coordinates = np.array(coordinates)

        for start, stop in zip(coordinates, coordinates[1:]):
            self.boundaries.append([start, stop])
            self.world.CreateStaticBody(
                shapes=B2D.b2EdgeShape(
                    vertices=[ensure_python(start), ensure_python(stop)]
                )
            )

    def add(self, cell):
        # Box2D only allows for 16 vertices per body,
        # and the current implementation would vastly exceed that
        # hence only simplifications
        assert PlacementSimulationSimplification.value != 0

        if PlacementSimulationSimplification.value == 2:
            shapes = [
                B2D.b2CircleShape(pos=offset, radius=radius)
                for radius, offset in cell.get_approximation_circles()
            ]
        else:
            shapes = [
                B2D.b2PolygonShape(
                    vertices=cell.raw_points(
                        simplify=PlacementSimulationSimplification.value == 1
                    ).tolist()
                )
            ]

        body = self.world.CreateDynamicBody(
            position=cell.position, angle=cell.angle, shapes=shapes
        )

        self.cell_bodies[cell] = body

    def remove(self, cell):
        self.world.DestroyBody(self.cell_bodies[cell])

        del self.cell_bodies[cell]

    def step(self, timestep):
        velocity_iter, position_iter = 6, 30
        self.world.Step(timestep, velocity_iter, position_iter)

        for cell, body in self.cell_bodies.items():
            cell.position = body.position[0], body.position[1]
            cell.angle = float(body.angle)
