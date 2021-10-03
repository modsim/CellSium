"""Simulation CLI entrypoint."""
import logging
import sys
from argparse import Namespace
from functools import partial, reduce
from time import time
from typing import Callable, Iterable, Iterator, Optional, Tuple, TypeVar

import numpy as np
from tunable import Tunable

from ...output import Output
from ...parameters import NewCellCount, h_to_s, s_to_h
from ...simulation.simulator import Simulator, Timestep, World
from .. import add_output_prefix, initialize_cells, initialize_simulator


class SimulationDuration(Tunable):
    """Time (simulated) the simulation should run"""

    default: float = 12.0


class SimulationOutputInterval(Tunable):
    """Time intervals (simulated) at which an output should be written"""

    default: float = 0.25


class SimulationTimestep(Tunable):
    """Time step at which the simulation state should be calculated"""

    default: float = 1.0 / 60.0


class SimulationOutputFirstState(Tunable):
    """Whether to output the first state"""

    default: bool = False


class BoundariesFile(Tunable):
    """Boundaries file (in DXF format) to add boundaries/geometrical constraints"""

    default: str = ""


class BoundariesScaleFactor(Tunable):
    """Scale factor for the boundaries"""

    default: float = 1.0


log = logging.getLogger(__name__)


def compose(*args):
    """
    Compose callable args.

    :param args: Args
    :return: Callable
    """
    return partial(reduce, lambda arg, fun: fun(arg), args)


def add_boundaries_from_dxf(
    file_name: str, simulator: Simulator, scale_factor: float = 1.0
) -> None:
    """
    Add boundaries from a DXF file.
    Supported are LWPolyline and Polyline objects.

    :param file_name: dxf file name
    :param simulator: Simulator instance to add the boundaries to
    :param scale_factor: Scale factor for the geometry
    :return: None
    """
    import ezdxf
    from ezdxf.entities import LWPolyline, Polyline

    dxf = ezdxf.readfile(file_name)

    for item in dxf.modelspace():
        points = None
        if isinstance(item, LWPolyline):
            points = np.array(list(item.get_points()))[:, :2]
        elif isinstance(item, Polyline):
            points = np.array(list(item.points()))[:, :2]
        else:
            log.warning("Warning, unknown type: %r", item.dxftype())

        if points is not None:
            points *= scale_factor

            simulator.add_boundary(points)


def add_boundaries_from_tunables(simulator: Simulator) -> Simulator:
    """
    Add boundaries to a simulator if the appropriate tunables are set.

    :param simulator: Simulator
    :return: Simulator
    """
    if BoundariesFile.value != '':
        add_boundaries_from_dxf(
            BoundariesFile.value, simulator, scale_factor=BoundariesScaleFactor.value
        )
    return simulator


def prepare_output_name(output_name: str, output: Output, prefix: str) -> str:
    """
    Prepare an output name.

    :param output_name: Output name
    :param output: Output object
    :param prefix: Prefix
    :return: Output name
    """
    if prefix:
        output_name = add_output_prefix(output_name, output=output)
    return output_name


def perform_outputs(
    world: World,
    simulation_time: float,
    outputs: Iterable[Output],
    output_name: Optional[str] = None,
    overwrite: bool = False,
    prefix: bool = False,
    output_count: int = 0,
) -> None:
    """
    Performs the output operations configured.

    :param world: World to output
    :param simulation_time: Simulation timepoint
    :param outputs: Outputs
    :param output_name: Name to output to
    :param overwrite: Whether to overwrite
    :param prefix: Whether to prefix the outputs with the name of the Output type
    :param output_count: The count of already outputted timesteps
    :return: None
    """
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


def initialize_output_times_from_tunables():
    """
    Initialize the duration, output_interval and last_output variables,
    from tunables.

    :return: duration, output_interval, last_output
    """
    duration = (
        h_to_s(SimulationDuration.value)
        if SimulationDuration.value > 0
        else float('inf')
    )

    output_interval = h_to_s(SimulationOutputInterval.value)

    if not SimulationOutputFirstState.value:
        last_output = 0.0
    else:
        last_output = -(h_to_s(SimulationOutputInterval.value) + sys.float_info.epsilon)

    return duration, output_interval, last_output


T = TypeVar('T')


def measure_duration(iterator: Iterator[T]) -> Iterator[Tuple[float, T]]:
    """
    Measure the (wall clock) time it takes to step forward the iterator,
    yielding the duration and iterator value.

    :param iterator: Iterator
    :return: Iterator of duration and iterator value
    """
    before = time()
    for value in iterator:
        after = time()
        yield (after - before), value
        before = time()


def perform_simulation(
    simulator: Optional[Simulator] = None,
    setup: Optional[Callable[[Simulator], Simulator]] = None,
    time_step: float = 1.0,
) -> Iterator[Timestep]:
    """
    Simple entrypoint to perform simulations.
    Will either accept a simulator instance or create one,
    call the setup callback on it if set,
    and then yield timesteps time_step apart indefinitely.

    :param simulator: Simulator
    :param setup: Setup callable
    :param time_step: Time step
    :return: Iterator of Timestep instances
    """
    if simulator is None:
        simulator = initialize_simulator()

    if setup:
        setup(simulator)

    while True:
        yield simulator.step(time_step)


def subcommand_main(args: Namespace) -> None:
    """
    Entry point for the 'simulate' subcommand.

    :param args: pre-parsed arguments
    :return: None
    """

    outputs = Output.SelectableGetMultiple()

    total_before = time()

    duration, output_interval, last_output = initialize_output_times_from_tunables()

    output_count = 0

    if duration == float('inf'):
        log.info("Simulation running in infinite mode ... press Ctrl-C to abort.")

    simulation_iterator = perform_simulation(
        setup=compose(
            add_boundaries_from_tunables,
            partial(initialize_cells, count=NewCellCount.value, cell_type=args.cell),
        ),
        time_step=h_to_s(SimulationTimestep.value),
    )

    interrupted = False
    try:
        for step_duration, ts in measure_duration(simulation_iterator):

            if ts.simulation.time > duration:
                break

            log.info(
                "Timestep took %.2fs, simulated time: %.2f h"
                % (step_duration, s_to_h(ts.simulation.time))
            )

            if (ts.simulation.time - last_output) >= output_interval > 0:
                last_output = ts.simulation.time

                perform_outputs(
                    ts.world,
                    ts.simulation.time,
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
