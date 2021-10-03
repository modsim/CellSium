"""Simulation package contains the simulation/simulator-related classes."""
import numpy as np


class BaseSimulator:
    def add(self, cell: object) -> None:
        """
        Add a cell to the simulation.

        :param cell: Cell
        :return: None
        """
        pass

    def remove(self, cell) -> None:
        """
        Remove a cell from the simulation.

        :param cell: Cell
        :return: None
        """
        pass

    def add_boundary(self, coordinates: np.ndarray) -> None:
        """
        Add a boundary to the simulation.

        :param coordinates: Coordinates of the boundary
        :return: None
        """
        pass

    def clear(self) -> None:
        """
        Clear the (world of the) simulation.

        :return: None
        """
        pass

    def step(self, timestep: float) -> None:
        """
        Advance the simulation by a timestep.

        :param timestep: Time passed in seconds
        :return: None
        """
        pass
