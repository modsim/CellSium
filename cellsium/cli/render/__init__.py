import argparse

import jsonpickle
from tunable import Tunable, TunableSelectable

from ...output.all import *
from .. import set_seed


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output-file', dest='output', default=None)
    parser.add_argument('-i', '--input-file', dest='input', default=None)

    TunableSelectable.setup_and_parse(parser)

    args = parser.parse_args()

    set_seed()

    output = Output()

    with open(args.input, 'r') as fp:
        data = fp.read()

    data = jsonpickle.decode(data)

    output.write(data, args.output)
