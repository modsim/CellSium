from pathlib import Path

from ..model import *
from ..simulation.placement import PlacementSimulation
from ..simulation.simulator import Simulator

# class Cell(PlacedCell, TimerCell):
#     pass


class Cell(PlacedCell, SizerCell):
    pass


def initialize_simulator():
    simulator = Simulator()
    ps = PlacementSimulation()

    simulator.sub_simulators += [ps]

    return simulator


def initialize_cells(simulator, count=0):
    cell_type = Cell

    random_sequences = cell_type.get_random_sequences()

    for _ in range(count):

        init_kwargs = {k: next(v) for k, v in random_sequences.items()}
        cell = cell_type(**init_kwargs)
        cell.birth()
        simulator.add(cell)


def add_output_prefix(output_name, output=None):
    output_name = Path(output_name)

    output_name = output_name.parent / (
        output.__class__.__name__ + '-' + output_name.name
    )

    return str(output_name)
