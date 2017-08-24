import pymunkoptions
pymunkoptions.options['debug'] = False
import pymunk

import numpy as np

from . import Simulator

from tunable import Tunable


class PlacementRadius(Tunable):
    default = 0.05


class PlacementSimulation(Simulator):

    verbose = False

    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = 0, 0

        self.cell_bodies = {}
        self.cell_shapes = {}

        self.boundaries = []

    def add_boundary(self, coordinates):
        coordinates = np.array(coordinates)
        new_body = pymunk.Body(body_type=pymunk.Body.STATIC)

        for start, stop in zip(coordinates, coordinates[1:]):
            self.boundaries.append([start, stop])
            segment = pymunk.Segment(new_body, start, stop, 0.0)
            self.space.add(segment)

        self.space.add(new_body)

    def add(self, cell):
        body = pymunk.Body(1.0, 1.0)
        body.position = pymunk.Vec2d((cell.position[0], cell.position[1]))
        body.angle = cell.angle

        points = cell.raw_points(simplify=False)

        if False:
            from matplotlib import pyplot
            pyplot.plot(points[:, 0], points[:, 1], marker='o')

            points = cell.raw_points(simplify=True)
            pyplot.plot(points[:, 0], points[:, 1], marker='o')

            pyplot.gca().set_aspect('equal', 'datalim')
            pyplot.show()
            points = cell.raw_points()

        shape = pymunk.Poly(body, points)
        shape.unsafe_set_radius(PlacementRadius.value)

        self.cell_bodies[cell] = body
        self.cell_shapes[cell] = shape

        self.space.add(body, shape)

    def remove(self, cell):
        self.space.remove(body, shape)

        del self.cell_bodies[cell]
        del self.cell_shapes[cell]

    def _get_positions(self):
        array = np.zeros((len(self.cell_bodies), 3))
        for n, body in enumerate(sorted(self.cell_bodies.values(), key=lambda body: id(body))):
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

    def simulate(self, time_step=0.1, iterations=9999, converge=True, epsilon=0.1):
        converging = False

        first_positions = self._get_positions()[:, :2]

        if converge:
            before_positions = first_positions.copy()

            for _ in range(iterations):
                self.space.step(time_step)
                after_positions = self._get_positions()[:, :2]

                dist = self._mean_distance(before_positions, after_positions) * time_step

                if True or self.verbose:
                    print(_, dist)

                if not converging:
                    if dist > 0:
                        converging = True
                        continue
                else:
                    if dist < epsilon:
                        break

                before_positions[:] = after_positions
        else:
            for _ in range(iterations):
                self.space.step(time_step)

            after_positions = self._get_positions()[:, :2]

        for cell, body in self.cell_bodies.items():
            cell.position = [body.position[0], body.position[1]]
            cell.angle = body.angle

        return self._total_distance(first_positions, after_positions)
