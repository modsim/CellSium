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

    simulation_end = 30 * 60 * 60  # 30 h
    simulation_end = 12 * 60 * 60  #
    simulation_output = 15 * 60  # 15 min

    simulation_timestep = 60  # 1 minute

    simulation_time = 0

    total_before = time()

    while simulation_time < simulation_end:
        before = time()
        simulator.step(simulation_timestep)
        simulation_time += simulation_timestep
        after = time()
        print("Timestep took %.2fs, virtual time: %.2f" % (after - before, simulation_time / (60.0 * 60.0)))

        if (simulation_time % simulation_output) == 0:
        #    output.display(simulator.simulation.world)
            pass

    total_after = time()
    print("Whole simulation took %.2fs" % (total_after - total_before))

    if args.output:
        output.write(simulator.simulation.world, args.output)
    else:
        output.display(simulator.simulation.world)
