import numpy as np

from ..parameters import s_to_h


class World:
    def __init__(self):
        self.cells = []
        self.boundaries = []

        self.cells_to_add = []
        self.cells_to_remove = []

    def add_boundary(self, coordinates):
        self.boundaries.append(np.array(coordinates))

    def clear(self):
        self.cells.clear()
        self.cells_to_add.clear()
        self.cells_to_remove.clear()
        self.boundaries.clear()

    def add(self, cell):
        self.cells_to_add.append(cell)

    def remove(self, cell):
        self.cells_to_remove.append(cell)

    def commit(self):
        for cell in self.cells_to_add:
            self.cells.append(cell)
        for cell in self.cells_to_remove:
            self.cells.remove(cell)

        self.cells_to_remove.clear()
        self.cells_to_add.clear()

    def copy(self):
        new_world = self.__class__()
        new_world.cells = self.cells[:]
        new_world.boundaries = self.boundaries[:]

        new_world.cells_to_add = self.cells_to_add[:]
        new_world.cells_to_remove = self.cells_to_remove[:]

        return new_world


class Simulation:
    def __init__(self):
        self.world = World()
        self.time = 0.0


class Timestep:
    __slots__ = 'timestep', 'simulation', 'simulator'

    @property
    def hours(self):
        return s_to_h(self.timestep)

    @property
    def time(self):
        return self.simulation.time

    @property
    def time_hours(self):
        return s_to_h(self.time)

    def __init__(self, timestep, simulation, simulator):
        self.timestep, self.simulation, self.simulator = timestep, simulation, simulator


class Simulator:
    def __init__(self):
        simulation = Simulation()
        self.simulation = simulation

        self.sub_simulators = []

    def add(self, cell):
        self.simulation.world.add(cell)

    def remove(self, cell):
        self.simulation.world.remove(cell)

    def add_boundary(self, coordinates):
        self.simulation.world.add_boundary(np.array(coordinates))

    def clear(self):
        self.simulation.world.clear()

    def step(self, timestep=0.0):

        simulation = self.simulation
        # possibly a deep copy if former states should be preserved?

        simulation.time += timestep

        ts = Timestep(timestep, simulation, self)

        simulation.world.commit()

        for cell in simulation.world.cells:
            cell.step(ts)

        simulation.world.commit()

        for sim in self.sub_simulators:
            sim.clear()

            for boundary in self.simulation.world.boundaries:
                sim.add_boundary(boundary)

            for cell in simulation.world.cells:
                sim.add(cell)

            sim.step(timestep)
