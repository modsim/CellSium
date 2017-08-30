from ..model import PlacedCell, SimulatedCell
from ..random import RRF
from ..parameters import Seed


def init():
    RRF.seed(Seed.value)


class Cell(PlacedCell, SimulatedCell):
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
        bend_lower=next(cpg.bend_lower)
    )
