import argparse

import numpy as np

from time import time
from tunable import Tunable, TunableSelectable

from . import Width, Height, Calibration
from .model import PlacedCell
from .random import RRF

from .simulation.placement import PlacementSimulation


from .output import Output

from .output.render import PlainRenderer
from .output.plot import PlotRenderer
from .output.svg import SvgRenderer
from .output.mesh import MeshOutput
from .output.tabular import *

from .parameters import CellParameterGenerator, Seed, NewCellCount


class BoundariesFile(Tunable):
    default = ""





class Simulation(object):
    def __init__(self):
        self.cells = set()
        self.boundaries = set()



class Simulator(object):
    def __init__(self):
        self.cells = set()
        self.sync = []

    def add(self, cell):
        self.cells.add(cell)
        for other in self.sync:
            other.add(cell)

    def remove(self, cell):
        self.cells.remove(cell)
        for other in self.sync:
            other.remove(cell)

    def sync_add(self, other):
        self.each_cell(other.add)
        self.sync.append(other)

    def cells(self):
        return iter(self.cells)

    def each_cell(self, callback):
        for cell in self.cells:
            callback(cell)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output-file', dest='output', default=None)

    TunableSelectable.setup_and_parse(parser)

    args = parser.parse_args()

    RRF.seed(Seed.value)

    cpg = CellParameterGenerator()

    CellType = PlacedCell

    def new_cell():
        length, width = 1, 2

        while width > length:
            length = next(cpg.length)
            width = next(cpg.width)

        return CellType(
            position=next(cpg.position),
            angle=next(cpg.angle),
            length=length,
            width=width,
            bend_overall=next(cpg.bend_overall),
            bend_upper=next(cpg.bend_upper),
            bend_lower=next(cpg.bend_lower)
        )

    simulator = Simulator()


    for _ in range(NewCellCount.value):
        simulator.add(new_cell())

    ps = PlacementSimulation()

    simulator.:
        ps.add(cell)

    before = time()

    boundaries = []

    if BoundariesFile.value != '':
        import ezdxf

        dxf = ezdxf.readfile(BoundariesFile.value)

        for item in dxf.modelspace():
            points = None
            if item.dxftype() == 'LWPOLYLINE':
                points = np.array(list(item.get_points()))[:, :2]
                points = points / 32 * 40
            elif item.dxftype() == 'POLYLINE':
                points = np.array(list(item.points()))
            else:
                print("Warning, unknown type", item.dxftype())

            boundaries.append(points)

    def add_boundaries_to(to, what):
        for w in what:
            to.add_boundary(w)

    add_boundaries_to(ps, boundaries)

    ps.simulate(time_step=0.1, epsilon=0.0000000001)

    after = time()
    print("Simulation time %.2fs" % (after - before))

    output = Output()

    add_boundaries_to(output, boundaries)

    for cell in cells:
        output.add(cell)

    if args.output:
        output.write(args.output)
    else:
        output.display()
