"""Training Generation CLI entrypoint."""
from argparse import Namespace

import tqdm
from tunable import Tunable, TunableManager

from ...output import Output
from ...parameters import pixel_to_um
from ...random import RRF
from .. import add_output_prefix, initialize_cells, initialize_simulator


class TrainingDataCount(Tunable):
    """Training samples to generate"""

    default: int = 16


class TrainingCellCount(Tunable):
    """Cells to add to training samples"""

    default: int = 32


class TrainingImageWidth(Tunable):
    """Image width in pixels of training images"""

    default: int = 128


class TrainingImageHeight(Tunable):
    """Image height in pixels of training images"""

    default: int = 128


tqdm.tqdm.monitor_interval = 0


def subcommand_main(args: Namespace) -> None:
    """
    Entry point for the 'training' subcommand.

    :param args: pre-parsed arguments
    :return: None
    """

    shape = (TrainingImageHeight.value, TrainingImageWidth.value)

    cell_count = TrainingCellCount.value

    TunableManager.load(
        {
            'Width': pixel_to_um(shape[1]),
            'Height': pixel_to_um(shape[0]),
            'NewCellRadiusFromCenter': 1,
        },
        reset=False,
    )

    ccf = RRF.sequence.integers(0, cell_count * 2)
    next(ccf)  # for seed = 1 and PCG64, the first value will be a zero ... skip that

    if not args.output:
        raise RuntimeError("Output must be set")

    outputs = Output.SelectableGetMultiple()

    output_count = 0

    for _ in tqdm.tqdm(range(TrainingDataCount.value)):
        simulator = initialize_simulator()
        initialize_cells(simulator, count=next(ccf))

        simulator.step(60.0)

        for output in outputs:
            if args.prefix:
                output_name = add_output_prefix(args.output, output=output)
            else:
                output_name = args.output

            output.write(
                simulator.simulation.world,
                output_name,
                overwrite=args.overwrite,
                output_count=output_count,
            )

        output_count += 1
