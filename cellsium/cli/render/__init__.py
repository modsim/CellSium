import jsonpickle

from ...output import Output


def subcommand_argparser(parser):
    """
    Handle the argument parser for the 'render' subcommand.

    :param parser: argument parser
    :return: None
    """
    parser.add_argument('-i', '--input-file', dest='input', default=None, required=True)


def subcommand_main(args):
    """
    Entrypoint for the 'render' subcommand.

    :param args: arguments to be passed
    :return:
    """
    output = Output()

    with open(args.input, 'r') as fp:
        data = fp.read()

    data = jsonpickle.decode(data)

    output.write(data, args.output)
