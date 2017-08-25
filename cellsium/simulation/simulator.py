import numpy as np


class World(object):
    def __init__(self):
        self.cells = []
        self.boundaries = []

    def add(self, cell):
        self.cells.append(cell)

    def remove(self, cell):
        self.cells.remove(cell)

    def add_boundary(self, coordinates):
        self.boundaries.append(np.array(coordinates))

    def clear(self):
        self.cells.clear()
        self.boundaries.clear()


class Simulation(object):
    def __init__(self):
        self.world = World()
        self.time = 0.0


class Timestep(object):
    __slots__ = 'timestep', 'simulation', 'simulator'

    def __init__(self, timestep, simulation, simulator):
        self.timestep, self.simulation, self.simulator = timestep, simulation, simulator


class Simulator(object):
    def __init__(self):
        simulation = Simulation()
        self.simulation = simulation

        self.sub_simulators = []

    def add(self, cell):
        self.simulation.world.add(cell)

        for sim in self.sub_simulators:
            sim.add(cell)

    def remove(self, cell):
        self.simulation.world.remove(cell)

        for sim in self.sub_simulators:
            sim.remove(cell)

    def add_boundary(self, coordinates):
        self.simulation.world.add_boundary(np.array(coordinates))

        for sim in self.sub_simulators:
            sim.add_boundary(coordinates)

    def clear(self):
        self.simulation.world.clear()

        for sim in self.sub_simulators:
            sim.clear()

    def step(self, timestep=0.0):

        simulation = self.simulation
        # possibly a deep copy if former states should be preserved?

        simulation.time += timestep

        ts = Timestep(timestep, simulation, self)

        for cell in simulation.world.cells:
            cell.step(ts)

        for cell in simulation.world.cells:
            self.remove(cell)
            self.add(cell)

        for sim in self.sub_simulators:
            sim.step(timestep)
