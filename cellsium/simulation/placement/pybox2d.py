# noinspection PyPep8Naming
import Box2D as B2D
import numpy as np

from .base import (
    PhysicalPlacement,
    PlacementSimulation,
    PlacementSimulationSimplification,
)


class Box2D(PhysicalPlacement, PlacementSimulation):

    verbose = False

    def __init__(self):
        self.world = B2D.b2World()
        self.world.gravity = 0, 0

        super().__init__()

    def add_boundary(self, coordinates):
        coordinates = np.array(coordinates)
        # self.world.CreateStaticBody(B2D.b2PolygonShape)

        for start, stop in zip(coordinates, coordinates[1:]):
            self.boundaries.append([start, stop])
            # segment = pymunk.Segment(new_body, start, stop, 0.0)
            # self.space.add(segment)

        # self.space.add(new_body)

    def add(self, cell):
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
                    )
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
