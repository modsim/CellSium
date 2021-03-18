import jsonpickle

from ...output.all import *


def subcommand_argparser(parser):
    parser.add_argument('-i', '--input-file', dest='input', default=None, required=True)


def subcommand_main(args):
    output = Output()

    with open(args.input, 'r') as fp:
        data = fp.read()

    data = jsonpickle.decode(data)

    output.write(data, args.output)
