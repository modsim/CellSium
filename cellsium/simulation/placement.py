import pymunkoptions
pymunkoptions.options['debug'] = False
import pymunk

import numpy as np

from . import BaseSimulator

from tunable import Tunable


class PlacementRadius(Tunable):
    default = 0.05


class PlacementSimulation(BaseSimulator):

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
        self.space.remove(self.cell_bodies[cell], self.cell_shapes[cell])

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

    def step(self, timestep):

        if False:
            from matplotlib import pyplot
            pyplot.ion()
            pyplot.close(pyplot.gcf())
            fig = pyplot.figure()
            ax = fig.add_subplot(111)

        resolution = 0.1
        times = timestep / resolution

        last = self.inner_step(time_step=resolution, iterations=int(times), epsilon=1e-12)

        if False:

            pyplot.waitforbuttonpress()
            from pymunk.matplotlib_util import DrawOptions

            self.space.debug_draw(DrawOptions(ax))
            fig.canvas.draw()
            fig.canvas.flush_events()

            pyplot.waitforbuttonpress()

    def inner_step(self, time_step=0.1, iterations=9999, converge=True, epsilon=0.1):
        converging = False

        first_positions = self._get_positions()[:, :2]

        lookback = 0
        lookback_max = 5

        if converge:
            before_positions = first_positions.copy()

            if False:

                from matplotlib import pyplot
                fig = pyplot.gcf()
                ax = pyplot.gca()

                scatter_plot = None
                print(iterations)
            for _ in range(iterations):
                self.space.step(time_step)
                after_positions = self._get_positions()[:, :2]

                if False:

                    if scatter_plot is None:
                        scatter_plot = ax.scatter(after_positions[:, 0], after_positions[:, 1])
                        pyplot.show()
                    else:
                        scatter_plot.set_offsets(after_positions)
                    import time
                    time.sleep(0.1)
                    fig.canvas.draw()
                    fig.canvas.flush_events()

                dist = self._mean_distance(before_positions, after_positions) * time_step

                before_positions[:] = after_positions

                if dist < epsilon:
                    lookback += 1
                    if lookback > lookback_max:
                        break
                else:
                    lookback = 0

                if lookback > lookback_max:
                    break

                if True or self.verbose:
                    print(_, dist)

                if not converging:
                    if dist > 0:
                        converging = True
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
