import tqdm
import argparse

from .. import new_cell, Cell, init
from ...output.all import *

from ...parameters import pixel_to_um
from ...parameters import CellParameterGenerator

from ...simulation.simulator import *
from ...simulation.placement import PlacementSimulation

from tunable import TunableSelectable, TunableManager, Tunable

tqdm.tqdm.monitor_interval = 0


cpg = None
ccf = None


def generate_training_data(cells=32, size=(128, 128), return_world=False, return_only_world=False):

    TunableManager.load({
        'Width': pixel_to_um(size[1]),
        'Height': pixel_to_um(size[0]),
        'NewCellRadiusFromCenter': 1
    }, reset=False)

    global cpg, ccf

    if cpg is None:
        cpg = CellParameterGenerator()
        ccf = RRF.new(np.random.randint, 0, cells*2)

    simulator = Simulator()
    ps = PlacementSimulation()

    simulator.sub_simulators += [ps]

    for _ in range(next(ccf)):
        cell = new_cell(cpg, Cell)
        cell.birth()
        simulator.add(cell)

    simulator.step(60.0)

    if return_only_world:
        return simulator.simulation.world

    image_gen, gt_gen = UnevenIlluminationPhaseContrast(), PlainRenderer()

    image = image_gen.convert(image_gen.output(simulator.simulation.world))

    gt = gt_gen.output(simulator.simulation.world)

    gt = gt > 0

    if return_world:
        return image, gt, simulator.simulation.world
    else:
        return image, gt


class TrainingDataCount(Tunable):
    default = 16


class TrainingCellCount(Tunable):
    default = 32


class TrainingImageWidth(Tunable):
    default = 128


class TrainingImageHeight(Tunable):
    default = 128


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-file', dest='output', default=None)
    TunableSelectable.setup_and_parse(parser)
    args = parser.parse_args()
    init()

    gtd_kwargs = dict(
        cells=TrainingCellCount.value,
        size=(TrainingImageHeight.value, TrainingImageWidth.value)
    )

    generate_training_data(**gtd_kwargs)

    if not args.output:
        raise RuntimeError("Output must be set")

    TiffOutput.channels = [NoisyUnevenIlluminationPhaseContrast]

    to = TiffOutput()
    for _ in tqdm.tqdm(range(TrainingDataCount.value)):
        world = generate_training_data(**gtd_kwargs,
                                       return_only_world=True)
        to.write(world, args.output)
