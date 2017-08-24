import argparse

import numpy as np

from time import time
from tunable import Tunable, TunableSelectable

from . import Width, Height, Calibration
from .model import PlacedCell, SimulatedCell
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


from .simulation.simulator import *


def add_boundaries_from_dxf(file_name, simulator):
    import ezdxf

    dxf = ezdxf.readfile(file_name)

    for item in dxf.modelspace():
        points = None
        if item.dxftype() == 'LWPOLYLINE':
            points = np.array(list(item.get_points()))[:, :2]
            points = points / 32 * 40
        elif item.dxftype() == 'POLYLINE':
            points = np.array(list(item.points()))
        else:
            print("Warning, unknown type", item.dxftype())

        simulator.add_boundary(points)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output-file', dest='output', default=None)

    TunableSelectable.setup_and_parse(parser)

    args = parser.parse_args()

    RRF.seed(Seed.value)

    cpg = CellParameterGenerator()

    class Cell(PlacedCell, SimulatedCell):
        pass

    CellType = Cell

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
    ps = PlacementSimulation()

    simulator.sub_simulators += [ps]

    if BoundariesFile.value != '':
        add_boundaries_from_dxf(BoundariesFile.value, simulator)

    for _ in range(NewCellCount.value):
        simulator.add(new_cell())

    output = Output()

    for n in range(0, 24):
        for _ in range(60):
            before = time()
            simulator.step(60.0)
            after = time()
            print("Simulation time %.2fs" % (after - before))

        output.display(simulator.simulation.world)

    if args.output:
        output.write(simulator.simulation.world, args.output)
    else:
        output.display(simulator.simulation.world)
