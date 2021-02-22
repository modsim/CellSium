from ..model import *
from ..parameters import Seed
from ..random import RRF


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
