import numpy as np
from tunable import Selectable, Tunable

from .. import BaseSimulator


class PlacementSimulationSimplification(Tunable):
    """How much the placement should be simplified,
    0: use the normal shapes,
    1: use simplified shapes,
    2: use many-circle approximations"""

    default = 0


class PlacementSimulation(BaseSimulator, Selectable):
    pass


class PhysicalPlacement(PlacementSimulation, PlacementSimulation.Virtual):
    def __init__(self):

        self.cell_bodies = {}
        self.cell_shapes = {}

        self.boundaries = []

    def clear(self):
        for cell in list(self.cell_bodies.keys()):
            self.remove(cell)

    def _get_positions(self):
        array = np.zeros((len(self.cell_bodies), 3))
        for n, body in enumerate(
            sorted(self.cell_bodies.values(), key=lambda body_: id(body_))
        ):
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


class NoPlacement(PlacementSimulation):
    pass
