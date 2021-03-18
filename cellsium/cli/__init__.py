import os

from ..model import *
from ..parameters import CellParameterGenerator, Seed
from ..random import RRF
from ..simulation.placement import PlacementSimulation
from ..simulation.simulator import Simulator


def set_seed(seed=None):
    if seed is None:
        seed = Seed.value
    RRF.seed(seed)
    return seed


# class Cell(PlacedCell, TimerCell):
#     pass


class Cell(PlacedCell, SizerCell):
    pass


def new_cell(cpg, cell_type):
    length, width = 1, 2

    while width > length:
        length = next(cpg.length)
        width = next(cpg.width)

    return cell_type(
        position=next(cpg.position),
        angle=next(cpg.angle),
        length=length,
        width=width,
        bend_overall=next(cpg.bend_overall),
        bend_upper=next(cpg.bend_upper),
        bend_lower=next(cpg.bend_lower),
    )


def initialize_simulator():
    simulator = Simulator()
    ps = PlacementSimulation()

    simulator.sub_simulators += [ps]

    return simulator


def initialize_cells(simulator, count=0, cpg=None):
    if cpg is None:
        cpg = CellParameterGenerator()

    for _ in range(count):
        cell = new_cell(cpg, Cell)
        cell.birth()
        simulator.add(cell)

    return cpg


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
