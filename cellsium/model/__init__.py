from .geometry import *


from math import log

class SimulatedCell(object):

    def grow(self, hours, ts):
        elongation_rate = 2 / 1.5  # 2 micrometer every 1.5 h
        self.length += elongation_rate * hours

        threshold = 3.5

        if self.length > threshold:
            self.divide(ts)

    def divide(self, ts):
        offspring_a, offspring_b = self.copy(), self.copy()

        offspring_a.position, offspring_b.position = self.get_division_positions()

        print("Division occurred!")

        offspring_a.length /= 2
        offspring_b.length /= 2

        ts.simulator.add(offspring_a)
        ts.simulator.add(offspring_b)

        ts.simulator.remove(self)


        if False:
            from matplotlib import pyplot
            pyplot.figure()
            p = self.points_on_canvas()
            pyplot.plot(p[:, 0], p[:, 1])
            p = offspring_a.points_on_canvas()
            pyplot.plot(p[:, 0], p[:, 1])
            p = offspring_b.points_on_canvas()
            pyplot.plot(p[:, 0], p[:, 1])
            pyplot.show()


    def step(self, ts):
        self.grow(hours=ts.timestep / (60.0 * 60.0), ts=ts)
