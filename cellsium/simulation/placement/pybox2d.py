from .base import PlacementSimulation, PlacementSimulationSimplification

import numpy as np
# noinspection PyPep8Naming
import Box2D as B2D


class Box2D(PlacementSimulation):

    verbose = False

    def __init__(self):
        self.world = B2D.b2World()
        self.world.gravity = 0, 0

        self.cell_bodies = {}
        self.cell_shapes = {}

        self.boundaries = []

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
                B2D.b2PolygonShape(vertices=cell.raw_points(simplify=PlacementSimulationSimplification.value == 1))
            ]

        body = self.world.CreateDynamicBody(
            position=cell.position,
            angle=cell.angle,
            shapes=shapes
        )

        self.cell_bodies[cell] = body

    def remove(self, cell):
        self.world.DestroyBody(self.cell_bodies[cell])

        del self.cell_bodies[cell]

    def clear(self):
        for cell in list(self.cell_bodies.keys()):
            self.remove(cell)

    def _get_positions(self):
        array = np.zeros((len(self.cell_bodies), 3))
        for n, body in enumerate(sorted(self.cell_bodies.values(), key=lambda body_: id(body_))):
            array[n, :] = body.position[0], body.position[1], body.angle
        return array

    @staticmethod
    def _all_distances(before, after):
        return np.sqrt(((after - before) ** 2).sum(axis=1))

    @classmethod
    def _total_distance(cls, before, after):
        return cls._all_distances(before, after).sum()

    @classmethod
    def _mean_distance(cls, before, after):
        return cls._all_distances(before, after).mean()

    def step(self, timestep):
        velocity_iter, position_iter = 6, 30
        self.world.Step(timestep, velocity_iter, position_iter)

        for cell, body in self.cell_bodies.items():
            cell.position = body.position[0], body.position[1]
            cell.angle = float(body.angle)
