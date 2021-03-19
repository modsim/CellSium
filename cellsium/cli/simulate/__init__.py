import logging
import sys
from time import time

import numpy as np
from tunable import Tunable

from ...output import Output
from ...parameters import NewCellCount, h_to_s, s_to_h
from .. import add_output_prefix, initialize_cells, initialize_simulator


class SimulationDuration(Tunable):
    default = 12.0


class SimulationOutputInterval(Tunable):
    default = 0.25


class SimulationTimestep(Tunable):
    default = 1.0 / 60.0


class SimulationOutputFirstState(Tunable):
    default = False


class BoundariesFile(Tunable):
    default = ""


log = logging.getLogger(__name__)


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


def subcommand_main(args):
    simulator = initialize_simulator()

    if BoundariesFile.value != '':
        add_boundaries_from_dxf(BoundariesFile.value, simulator)

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
        while (
            simulation_time < h_to_s(SimulationDuration.value)
            or SimulationDuration.value < 0
        ):
            before = time()

            simulator.step(time_step)

            simulation_time += time_step
            after = time()

            log.info(
                "Timestep took %.2fs, virtual time: %.2f h"
                % (after - before, s_to_h(simulation_time))
            )

            if SimulationOutputInterval.value > 0:
                if (simulation_time - last_output) >= h_to_s(
                    SimulationOutputInterval.value
                ):
                    last_output = simulation_time

                    log.debug(
                        "Outputting simulation state at %.2f h"
                        % (s_to_h(simulation_time),)
                    )

                    for output in outputs:
                        output_before = time()
                        if args.output:
                            if args.prefix:
                                output_name = add_output_prefix(
                                    args.output, output=output
                                )
                            output.write(
                                simulator.simulation.world,
                                output_name,
                                time=simulation_time,
                                output_count=output_count,
                                overwrite=args.overwrite,
                            )
                        else:
                            output.display(simulator.simulation.world)
                        output_after = time()

                        log.debug(
                            "Output %s took %.2fs"
                            % (output.__class__.__name__, output_after - output_before)
                        )

                    output_count += 1
    except KeyboardInterrupt:
        log.info("Ctrl-C pressed, stopping simulation.")
        interrupted = True

    total_after = time()
    log.info(
        "%s simulation took %.2fs"
        % (("Whole" if not interrupted else "Interrupted"), total_after - total_before)
    )
