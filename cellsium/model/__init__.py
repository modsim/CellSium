from .geometry import *


import numpy as np
from math import log
from ..random import RRF

threshold_series = RRF.new(np.random.uniform, 3.0, 4.0)
elongation_rate_series = RRF.new(np.random.uniform, 1, 2)


class SimulatedCell(object):
    @staticmethod
    def defaults():
        return dict(_threshold=lambda: next(threshold_series), _gr=lambda: next(elongation_rate_series))

    def grow(self, hours, ts):
        #elongation_rate = 2 / 1.5  # 2 micrometer every 1.5 h
        elongation_rate = self._gr
        self.length += elongation_rate * hours

        threshold = self._threshold

        if self.length > threshold:
            offspring_a, offspring_b = self.divide(ts)
            offspring_a.length /= 2
            offspring_b.length /= 2

            offspring_a._gr = next(elongation_rate_series)
            offspring_b._gr = next(elongation_rate_series)

    def divide(self, ts):
        offspring_a, offspring_b = self.copy(), self.copy()

        offspring_a.position, offspring_b.position = self.get_division_positions()

        if hasattr(self, 'id_'):
            offspring_a.parent_id = offspring_b.parent_id = self.id_

        ts.simulator.add(offspring_a)
        ts.simulator.add(offspring_b)

        ts.simulator.remove(self)

        return offspring_a, offspring_b

    def step(self, ts):
        self.grow(hours=ts.timestep / (60.0 * 60.0), ts=ts)
