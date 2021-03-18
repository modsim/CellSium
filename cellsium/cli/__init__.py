import os

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


def generate_output_name(args, output_count=0, output=None):
    try:
        output_name = args.output % (output_count,)
    except TypeError:
        output_name = args.output

    if args.prefix and output:
        output_name = os.path.join(
            os.path.dirname(output_name),
            output.__class__.__name__ + '-' + os.path.basename(output_name),
        )

    return output_name
