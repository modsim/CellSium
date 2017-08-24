from .geometry import *


class Timestep(object):
    __slots__ = 'timestep', 'absolute_time', 'simulator'

    def __init__(self, timestep, absolute_time, simulator):
        self.timestep, self.absolute_time, self.simulator = timestep, absolute_time, simulator


class SimulatedCell(object):
    def step(self, ts):
        pass
