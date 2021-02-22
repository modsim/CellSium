import os
import sys
import argparse
import logging

from time import time
from tunable import TunableSelectable

from ..simulation.placement import PlacementSimulation

from ..simulation.simulator import Simulator

from ..output.all import *

from ..parameters import CellParameterGenerator, NewCellCount, h_to_s, s_to_h

from . import Cell, set_seed

from . import new_cell

log = logging.getLogger(__name__)


class BoundariesFile(Tunable):
    default = ""


class SimulationDuration(Tunable):
    default = 12.0


class SimulationOutputInterval(Tunable):
    default = 0.25


class SimulationTimestep(Tunable):
    default = 1.0 / 60.0


class SimulationOutputFirstState(Tunable):
    default = False


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


def parse_arguments_and_init():
    logging.basicConfig(level=logging.INFO, format="%(asctime)-15s.%(msecs)03d %(name)s %(levelname)s %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S')

    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output-file', dest='output', default=None)
    parser.add_argument('-w', '--overwrite', dest='overwrite', default=False, action='store_true')
    parser.add_argument('-p', '--prefix', dest='prefix', default=False, action='store_true')
    verbose_group = parser.add_mutually_exclusive_group()
    verbose_group.add_argument('-q', '--quiet', dest='quiet', default=False, action='store_true')
    verbose_group.add_argument('-v', '--verbose', dest='verbose', default=1, action='count')

    TunableSelectable.setup_and_parse(parser)

    args = parser.parse_args()

    if args.quiet:
        log.setLevel(logging.WARNING)
    elif args.verbose == 1:
        log.setLevel(logging.INFO)
    else:
        # possibly switch on more debug settings
        log.setLevel(logging.DEBUG)

    return args


def initialize_simulator():
    simulator = Simulator()
    ps = PlacementSimulation()

    simulator.sub_simulators += [ps]

    if BoundariesFile.value != '':
        add_boundaries_from_dxf(BoundariesFile.value, simulator)

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
            output.__class__.__name__ + '-' + os.path.basename(output_name)
        )

    return output_name

def main():
    args = parse_arguments_and_init()

    seed = set_seed()
    log.info("Seeding with %s" % (seed,))

    simulator = initialize_simulator()

    initialize_cells(simulator, count=NewCellCount.value)

    outputs = Output.SelectableGetMultiple()

    simulation_time = 0.0

    last_output = 0.0

    if SimulationOutputFirstState.value:
        last_output = -(h_to_s(SimulationOutputInterval.value) + sys.float_info.epsilon)

    total_before = time()

    time_step = h_to_s(SimulationTimestep.value)

    output_count = 0

    if SimulationDuration.value < 0:
        log.info("Simulation running in infinite mode ... press Ctrl-C to abort.")

    interrupted = False
    try:
        while simulation_time < h_to_s(SimulationDuration.value) or SimulationDuration.value < 0:
            before = time()

            simulator.step(time_step)

            simulation_time += time_step
            after = time()

            log.info("Timestep took %.2fs, virtual time: %.2f h" % (after - before, s_to_h(simulation_time)))

            if SimulationOutputInterval.value > 0:
                if (simulation_time - last_output) >= h_to_s(SimulationOutputInterval.value):
                    last_output = simulation_time

                    log.debug("Outputting simulation state at %.2f h" % (s_to_h(simulation_time),))

                    for output in outputs:
                        output_before = time()
                        if args.output:
                            output_name = generate_output_name(args, output_count=output_count, output=output)
                            output.write(simulator.simulation.world, output_name, time=simulation_time,
                                         overwrite=args.overwrite)
                        else:
                            output.display(simulator.simulation.world)
                        output_after = time()

                        log.debug("Output %s took %.2fs" % (output.__class__.__name__, output_after - output_before))

                    output_count += 1
    except KeyboardInterrupt:
        log.info("Ctrl-C pressed, stopping simulation.")
        interrupted = True

    total_after = time()
    log.info("%s simulation took %.2fs" % (("Whole" if not interrupted else "Interrupted"), total_after - total_before))
