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


class BoundariesScaleFactor(Tunable):
    default = 1.0


log = logging.getLogger(__name__)


def add_boundaries_from_dxf(file_name, simulator, scale_factor=1.0):
    import ezdxf

    dxf = ezdxf.readfile(file_name)

    for item in dxf.modelspace():
        points = None
        if item.dxftype() == 'LWPOLYLINE':
            points = np.array(list(item.get_points()))[:, :2]
        elif item.dxftype() == 'POLYLINE':
            points = np.array(list(item.points()))[:, :2]
        else:
            log.warning("Warning, unknown type: %r", item.dxftype())

        if points is not None:
            points *= scale_factor

            simulator.add_boundary(points)


def prepare_output_name(output_name, output, prefix):
    if prefix:
        output_name = add_output_prefix(output_name, output=output)
    return output_name


def perform_outputs(
    world,
    simulation_time,
    outputs,
    output_name=None,
    overwrite=False,
    prefix=False,
    output_count=0,
):
    log.debug("Outputting simulation state at %.2f h" % (s_to_h(simulation_time),))
    for output in outputs:
        output_before = time()

        if output_name:
            output.write(
                world,
                prepare_output_name(output_name, output, prefix),
                time=simulation_time,
                output_count=output_count,
                overwrite=overwrite,
            )
        else:
            output.display(world)

        output_after = time()

        log.debug(
            "Output %s took %.2fs"
            % (output.__class__.__name__, output_after - output_before)
        )


def subcommand_main(args):
    simulator = initialize_simulator()

    if BoundariesFile.value != '':
        add_boundaries_from_dxf(
            BoundariesFile.value, simulator, scale_factor=BoundariesScaleFactor.value
        )

    initialize_cells(simulator, count=NewCellCount.value)

    outputs = Output.SelectableGetMultiple()

    simulation_time = 0.0

    last_output = 0.0

    if SimulationOutputFirstState.value:
        last_output = -(h_to_s(SimulationOutputInterval.value) + sys.float_info.epsilon)

    total_before = time()

    time_step = h_to_s(SimulationTimestep.value)
    duration = (
        h_to_s(SimulationDuration.value)
        if SimulationDuration.value > 0
        else float('inf')
    )
    output_interval = h_to_s(SimulationOutputInterval.value)

    output_count = 0

    if duration == float('inf'):
        log.info("Simulation running in infinite mode ... press Ctrl-C to abort.")

    interrupted = False
    try:
        while simulation_time < duration:

            before = time()

            simulator.step(time_step)
            simulation_time += time_step

            after = time()

            log.info(
                "Timestep took %.2fs, simulated time: %.2f h"
                % (after - before, s_to_h(simulation_time))
            )

            if (simulation_time - last_output) >= output_interval > 0:

                last_output = simulation_time

                perform_outputs(
                    simulator.simulation.world,
                    simulation_time,
                    outputs,
                    args.output,
                    overwrite=args.overwrite,
                    prefix=args.prefix,
                    output_count=output_count,
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
