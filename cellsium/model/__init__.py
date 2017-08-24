from .geometry import *


from math import log

class SimulatedCell(object):

    def grow(self, hours, ts):
        elongation_rate = 2 / 1.5  # 2 micrometer every 1.5 h
        self.length += elongation_rate * hours

        threshold = 8.0

        if self.length > threshold:
            self.divide(ts)

    def divide(self, ts):
        offspring_a, offspring_b = self.copy(), self.copy()

        print("Division occurred!")

        offspring_a.length /= 2
        offspring_b.length /= 2

        ts.simulator.add(offspring_a)
        ts.simulator.add(offspring_b)

        ts.simulator.remove(self)

    def step(self, ts):
        self.grow(hours=ts.timestep / (60.0 * 60.0), ts=ts)
