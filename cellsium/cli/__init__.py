"""CLI package, home to the individual entry points"""
from pathlib import Path
from typing import Any, Optional

from ..model import PlacedCell, SizerCell, TimerCell
from ..output import Output
from ..simulation.placement import PlacementSimulation
from ..simulation.simulator import Simulator


class TimerCell(PlacedCell, TimerCell):
    """Cell."""

    pass


class SizerCell(PlacedCell, SizerCell):
    """Cell."""


Cell = SizerCell


def initialize_simulator() -> Simulator:
    """
    Constructor helper for a simulator.

    :return: Simulator instance
    """
    simulator = Simulator()
    ps = PlacementSimulation()

    simulator.sub_simulators += [ps]

    return simulator


def initialize_cells(
    simulator: Simulator,
    count: int = 1,
    cell_type: Optional[PlacedCell] = None,
    sequence: Any = None,
) -> Simulator:
    """
    Initialize cells and add them to a simulator.

    :param simulator: Simulator to add cells to.
    :param count: Count of cells to generate
    :param cell_type: cell type to use
    :param sequence: Random number sequence to use
    :return: Simulator
    """
    if cell_type is None:
        cell_type = Cell

    random_sequences = cell_type.get_random_sequences(sequence=sequence)

    for _ in range(count):

        init_kwargs = {k: next(v) for k, v in random_sequences.items()}

        # handling for items which are generated jointly,
        # but need to go to separate kwargs
        for k, v in list(init_kwargs.items()):
            if "__" in k:
                del init_kwargs[k]
                k_fragments = k.split("__")
                for inner_k, inner_v in zip(k_fragments, v):
                    init_kwargs[inner_k] = inner_v

        cell = cell_type(**init_kwargs)
        cell.birth()
        simulator.add(cell)

    return simulator


def add_output_prefix(output_name: str, output: Output) -> str:
    """
    Adds an prefix to an output filename.

    :param output_name: Output name
    :param output: Output object
    :return: Name
    """
    output_name = Path(output_name)

    output_name = output_name.parent / (
        output.__class__.__name__ + "-" + output_name.name
    )

    return str(output_name)
