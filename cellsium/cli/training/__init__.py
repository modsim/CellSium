import tqdm
import argparse

import numpy as np

from .. import new_cell, Cell, init
from ...output.all import *

from ... import Width, Height, Calibration, um_to_pixel, pixel_to_um
from ...parameters import CellParameterGenerator, Seed, NewCellCount

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
        simulator.add(new_cell(cpg, Cell))

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-file', dest='output', default=None)
    TunableSelectable.setup_and_parse(parser)
    args = parser.parse_args()
    init()

    generate_training_data()

    if args.output:
        TiffOutput.channels = [NoisyUnevenIlluminationPhaseContrast]

        to = TiffOutput()
        for _ in tqdm.tqdm(range(TrainingDataCount.value)):
            world = generate_training_data(return_only_world=True)
            to.write(world, args.output)

        print("Done")
        raise SystemExit

    show = False

    from time import time

    if show:

        from matplotlib import pyplot

        fig = pyplot.figure()

        ax = fig.add_axes([0, 0, 1, 1])

        aximg = None

    else:
        print("Processing")
        before = time()
        counter = 0

    try:

        while True:
            image, gt = generate_training_data()

            if not show:
                counter += 1
            else:

                image = np.r_[image, (gt*255).astype(np.uint8)]

                if aximg is None:
                    aximg = ax.imshow(image, cmap='gray')
                else:
                    aximg.set_data(image)

                fig.canvas.draw()

                pyplot.waitforbuttonpress()

    except KeyboardInterrupt:
        after = time()
        print("Did %d steps in %.2fs, i.e. %.2fs per step" % (counter, (after-before), (after-before)/counter))