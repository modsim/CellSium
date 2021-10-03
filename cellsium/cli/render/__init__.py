"""Rendering CLI utility, render a simulation state saved using jsonpickle."""

from argparse import ArgumentParser, Namespace

import jsonpickle

from ...output import Output


def subcommand_argparser(parser: ArgumentParser) -> None:
    """
    Handle the argument parser for the 'render' subcommand.

    :param parser: Argument parser
    :return: None
    """
    parser.add_argument('-i', '--input-file', dest='input', default=None, required=True)


def subcommand_main(args: Namespace) -> None:
    """
    Entry point for the 'render' subcommand.

    :param args: Pre-parsed arguments
    :return: None
    """
    output = Output()

    with open(args.input, 'r') as fp:
        data = fp.read()

    data = jsonpickle.decode(data)

    output.write(data, args.output)
