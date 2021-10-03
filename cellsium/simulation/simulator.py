"""Simulator base classes."""

import numpy as np

from ..parameters import s_to_h
from . import BaseSimulator


class World:
    """The World class contains the cells and, if present, the boundaries."""

    def __init__(self):
        self.cells = []
        self.boundaries = []

        self.cells_to_add = []
        self.cells_to_remove = []

    def add_boundary(self, coordinates: np.ndarray) -> None:
        """
        Add a boundary to the simulation.

        :param coordinates: Coordinates of the boundary.
        :return: None
        """
        self.boundaries.append(np.array(coordinates))

    def clear(self) -> None:
        """
        Resets the World.

        :return: None
        """
        self.cells.clear()
        self.cells_to_add.clear()
        self.cells_to_remove.clear()
        self.boundaries.clear()

    def add(self, cell: object) -> None:
        """
        Adds a cell to the World.

        :param cell: Cell
        :return: None
        """
        self.cells_to_add.append(cell)

    def remove(self, cell: object) -> None:
        """
        Removes a cell from the world.

        :param cell: Cell
        :return: None
        """
        self.cells_to_remove.append(cell)

    def commit(self) -> None:
        """
        Commits a step. Cells to be added, and cells to be removed,
        will only be applied once commit is called.

        :return: None
        """
        for cell in self.cells_to_add:
            self.cells.append(cell)
        for cell in self.cells_to_remove:
            self.cells.remove(cell)

        self.cells_to_remove.clear()
        self.cells_to_add.clear()

    def copy(self) -> "World":
        """
        Creates a copy of thw World.

        :return: Copy of the World
        """
        new_world = self.__class__()
        new_world.cells = self.cells[:]
        new_world.boundaries = self.boundaries[:]

        new_world.cells_to_add = self.cells_to_add[:]
        new_world.cells_to_remove = self.cells_to_remove[:]

        return new_world


class Simulation:
    """Simulation represents the simulation state at a certain timepoint,
    i.e. a World and a time."""

    def __init__(self):
        self.world = World()
        self.time = 0.0


class Timestep:
    """Timestep is an auxiliary class combining a certain
    timepoint, simulation and simulator."""

    __slots__ = "timestep", "simulation", "simulator"

    @property
    def hours(self) -> float:
        """
        The hours passed within this timestep.

        :return: Hours
        """
        return s_to_h(self.timestep)

    @property
    def time(self) -> float:
        """
        Total simulation time passed in seconds.

        :return: Seconds
        """
        return self.simulation.time

    @property
    def time_hours(self) -> float:
        """
        Total simulation time passed in hours.

        :return: Hours
        """
        return s_to_h(self.time)

    @property
    def world(self) -> World:
        return self.simulation.world

    def __init__(self, timestep: float, simulation: Simulation, simulator: "Simulator"):
        self.timestep, self.simulation, self.simulator = timestep, simulation, simulator


class Simulator(BaseSimulator):
    """Simulator class, a class serving as interface to World and sub-simulators
    (such as physical placement), as well as the caller of each cells step function."""

    def __init__(self):
        simulation = Simulation()
        self.simulation = simulation

        self.sub_simulators = []

    def add(self, cell: object) -> None:

        self.simulation.world.add(cell)

    def remove(self, cell: object) -> None:

        self.simulation.world.remove(cell)

    def add_boundary(self, coordinates: np.ndarray) -> None:

        self.simulation.world.add_boundary(np.array(coordinates))

    def clear(self) -> None:

        self.simulation.world.clear()

    def step(self, timestep: float = 0.0) -> Timestep:

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

        return ts
