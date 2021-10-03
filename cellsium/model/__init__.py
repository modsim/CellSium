"""Cell model package."""
from typing import Any, Iterable, Mapping, Optional

from ..parameters import h_to_s, s_to_h
from ..simulation.simulator import Timestep
from .agent import (
    Copyable,
    IdCounter,
    InitializeWithParameters,
    Representable,
    WithLineage,
    WithLineageHistory,
    WithRandomSequences,
    WithTemporalLineage,
)
from .geometry import (
    AutoMesh3D,
    BentRod,
    CellGeometry,
    Coccoid,
    Ellipsoid,
    Rectangle,
    RodShaped,
    Shape,
    Shape3D,
    Square,
    WithAngle,
    WithFluorescence,
    WithPosition,
    WithProperDivisionBehavior,
)
from .initialization import (
    RandomAngle,
    RandomBentRod,
    RandomPosition,
    RandomWidthLength,
)


def generate_cell(*additional_classes: type, name: str = "PlacedCell"):
    """
    Generates a cell class using the standard classes, and possible additional classes.

    :param additional_classes: Additional classes to inherit the cell from.
    :param name: Name of the class
    :return: Class
    """
    cell = type(
        name,
        (
            WithLineageHistory,
            WithLineage,
            WithTemporalLineage,
            WithProperDivisionBehavior,
            InitializeWithParameters,
            Copyable,
            Representable,
            WithRandomSequences,
            RandomWidthLength,
            RandomBentRod,
            RandomPosition,
            RandomAngle,
            CellGeometry,
        )
        + additional_classes,
        {},
    )

    return cell


PlacedCell = generate_cell(BentRod)


class SimulatedCell:
    """
    Base class for simulated cells, allowing for division behavior.
    """

    def birth(
        self, parent: Optional["SimulatedCell"] = None, ts: Optional[Timestep] = None
    ) -> None:
        """
        Called when a cell is "born".

        :param parent: Parent cell
        :param ts: Timestep
        :return: None
        """
        pass

    def grow(self, ts: Timestep) -> None:
        """
        Called each timestep to grow cell.

        :param ts: Timestep
        :return: None
        """
        pass

    def divide(self, ts: Timestep) -> Iterable["SimulatedCell"]:
        """
        Called when a cell should divide, creates the daughter cells.

        :param ts: Timestep
        :return: None
        """
        offspring_a, offspring_b = self.copy(), self.copy()

        offspring_a.position, offspring_b.position = self.get_division_positions()

        if isinstance(self, WithLineage):
            offspring_a.parent_id = offspring_b.parent_id = self.id_

        if isinstance(self, WithLineageHistory):
            offspring_a.lineage_history = self.lineage_history[:] + [self.id_]
            offspring_b.lineage_history = self.lineage_history[:] + [self.id_]

        if isinstance(self, WithTemporalLineage):
            now = ts.simulation.time
            offspring_b.birth_time = offspring_a.birth_time = now

        ts.simulator.add(offspring_a)
        ts.simulator.add(offspring_b)

        offspring_a.birth(parent=self, ts=ts)
        offspring_b.birth(parent=self, ts=ts)

        ts.simulator.remove(self)

        return offspring_a, offspring_b

    def step(self, ts: Timestep) -> None:
        """
        Timestep function of the cell object, called by the simulator.

        :param ts: Timestep
        :return: None
        """
        self.grow(ts=ts)


# noinspection PyAttributeOutsideInit
class SizerCell(SimulatedCell):
    """
    Example cell implementing a simple sizer growth mechanism.
    """

    @staticmethod
    def random_sequences(sequence: Any) -> Mapping[str, Any]:
        return dict(division_size=sequence.normal(3.0, 0.25))  # µm

    def birth(
        self, parent: Optional["SizerCell"] = None, ts: Optional[Timestep] = None
    ) -> None:
        self.division_size = next(self.random.division_size)
        self.elongation_rate = 1.5

    def grow(self, ts: Timestep) -> None:
        self.length += self.elongation_rate * ts.hours

        if self.length > self.division_size:
            offspring_a, offspring_b = self.divide(ts)
            offspring_a.length = offspring_b.length = self.length / 2


# noinspection PyAttributeOutsideInit
class TimerCell(SimulatedCell):
    """
    Example cell implementing a simple timer growth mechanism.
    """

    @staticmethod
    def random_sequences(sequence: Any) -> Mapping[str, Any]:
        return dict(elongation_rate=sequence.normal(1.5, 0.25))  # µm·h⁻¹

    def birth(
        self, parent: Optional["TimerCell"] = None, ts: Optional[Timestep] = None
    ) -> None:
        self.elongation_rate = next(self.random.elongation_rate)
        self.division_time = h_to_s(1.0)

    def grow(self, ts: Timestep) -> None:
        self.length += self.elongation_rate * ts.hours

        if ts.time > (self.birth_time + self.division_time):
            offspring_a, offspring_b = self.divide(ts)
            offspring_a.length = offspring_b.length = self.length / 2


__all__ = [
    'InitializeWithParameters',
    'WithRandomSequences',
    'Copyable',
    'Representable',
    'IdCounter',
    'WithLineage',
    'WithLineageHistory',
    'WithTemporalLineage',
    'Shape',
    'Shape3D',
    'RodShaped',
    'Rectangle',
    'Square',
    'BentRod',
    'Coccoid',
    'Ellipsoid',
    'WithPosition',
    'WithAngle',
    'WithFluorescence',
    'WithProperDivisionBehavior',
    'AutoMesh3D',
    'CellGeometry',
    's_to_h',
    'h_to_s',
    'PlacedCell',
    'SimulatedCell',
    'TimerCell',
    'SizerCell',
    'generate_cell',
]
