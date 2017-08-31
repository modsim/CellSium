from .. import s_to_h, h_to_s
from .agent import *
from .geometry import *


import numpy as np
from math import log
from ..random import RRF


class PlacedCell(WithLineage, WithTemporalLineage, WithProperDivisionBehavior, InitializeWithParameters, Copyable, CellGeometry, BentRod):
    pass


class SimulatedCell(object):

    def birth(self, parent=None, ts=None):
        pass

    def grow(self, ts):
        pass

    def divide(self, ts):
        offspring_a, offspring_b = self.copy(), self.copy()

        offspring_a.position, offspring_b.position = self.get_division_positions()

        if isinstance(self, WithLineage):
            offspring_a.parent_id = offspring_b.parent_id = self.id_

        if isinstance(self, WithTemporalLineage):
            now = ts.simulation.time
            offspring_b.birth_time = offspring_a.birth_time = now

        ts.simulator.add(offspring_a)
        ts.simulator.add(offspring_b)

        offspring_a.birth(parent=self, ts=ts)
        offspring_b.birth(parent=self, ts=ts)

        ts.simulator.remove(self)

        return offspring_a, offspring_b

    def step(self, ts):
        self.grow(ts=ts)


class SizerCell(SimulatedCell):
    sizer_series = RRF.new(np.random.normal, 3.0, 0.25)  # µm

    def birth(self, parent=None, ts=None):
        self.division_size = next(self.__class__.sizer_series)
        self.elongation_rate = 1.5

    def grow(self, ts):
        self.length += self.elongation_rate * ts.hours

        if self.length > self.division_size:
            offspring_a, offspring_b = self.divide(ts)
            offspring_a.length = offspring_b.length = self.length / 2


class TimerCell(SimulatedCell):
    elongation_rate_series = RRF.new(np.random.normal, 1.5, 0.25)  # µm·h⁻¹

    def birth(self, parent=None, ts=None):
        self.division_time = h_to_s(1.0)
        self.elongation_rate = next(self.__class__.elongation_rate_series)

    def grow(self, ts):
        self.length += self.elongation_rate * ts.hours

        if ts.time > (self.birth_time + self.division_time):
            offspring_a, offspring_b = self.divide(ts)
            offspring_a.length = offspring_b.length = self.length / 2
