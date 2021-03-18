import numpy as np
import tqdm
from tunable import Tunable, TunableManager

from ...output import Output
from ...parameters import pixel_to_um
from ...random import RRF
from .. import generate_output_name, initialize_cells, initialize_simulator


class TrainingDataCount(Tunable):
    default = 16


class TrainingCellCount(Tunable):
    default = 32


class TrainingImageWidth(Tunable):
    default = 128


class TrainingImageHeight(Tunable):
    default = 128


tqdm.tqdm.monitor_interval = 0


def subcommand_main(args):
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

    ccf = RRF.new(np.random.randint, 0, cell_count * 2)

    if not args.output:
        raise RuntimeError("Output must be set")

    outputs = Output.SelectableGetMultiple()

    cpg = None

    output_count = 0

    for _ in tqdm.tqdm(range(TrainingDataCount.value)):
        simulator = initialize_simulator()
        cpg = initialize_cells(simulator, count=next(ccf), cpg=cpg)

        simulator.step(60.0)

        for output in outputs:
            output_name = generate_output_name(
                args, output_count=output_count, output=output
            )
            output.write(
                simulator.simulation.world, output_name, overwrite=args.overwrite
            )

        output_count += 1
