import argparse

from tunable import Tunable, TunableSelectable

from ...output.all import *

from jsonpickle import loads

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output-file', dest='output', default=None)
    parser.add_argument('-i', '--input-file', dest='input', default=None)

    TunableSelectable.setup_and_parse(parser)

    args = parser.parse_args()

    output = Output()

    with open(args.input, 'r') as fp:
        data = fp.read()

    data = loads(data)

    print(data.cells)

    output.write(data, args.output)

