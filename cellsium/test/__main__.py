# -*- coding: utf-8 -*-
"""
The test module's __main__ contains the main() function to run the doctests.
"""

import sys
import doctest

from types import ModuleType


def collect_modules_recursive(start, blacklist=None):
    """
    Collects all modules and submodules in a recursive manner.

    :param start: the top module to start from
    :param blacklist: a string or list of strings of module (sub)names which should be ignored.
    :return:
    """

    if not isinstance(blacklist, list):
        blacklist = [blacklist]

    collector = set()

    def _inner(current):
        collector.add(current)
        for another in dir(current):
            another = getattr(current, another)
            if isinstance(another, ModuleType):
                if another.__name__.startswith(start.__name__):

                    ok = True
                    for blacklisted in blacklist:
                        if blacklisted in another.__name__:
                            ok = False

                    if ok:
                        _inner(another)

    _inner(start)

    return list(sorted(collector, key=lambda module: module.__name__))


def run_tests_recursively(start_module, blacklist=None, exit=True, quiet=False):
    """
    Runs doctests recursively.

    :param start_module: the top module to start from
    :param blacklist: a string or list of strings of module (sub)names which should be ignored.
    :param exit: whether to exit with return code
    :param quiet: whether to print infos about tests
    :return:
    """
    total_failures, total_tests = 0, 0

    for a_module in collect_modules_recursive(start_module, blacklist):
        failures, tests = doctest.testmod(a_module)
        total_failures += failures
        total_tests += tests

    if not quiet:
        print("Run %d tests in total." % (total_tests,))

    if total_failures > 0:
        if not quiet:
            print("Test failures occurred, exiting with non-zero status.")

        if exit:
            sys.exit(1)


# noinspection PyUnresolvedReferences
def main():
    """
    Runs all the doctests.

    """

    import cellsium.cli.render
    import cellsium.cli.training
    import cellsium.cli.cli

    import cellsium.geometry

    import cellsium.model
    import cellsium.model.agent
    import cellsium.model.geometry

    import cellsium.output
    import cellsium.output.all

    import cellsium.simulation
    import cellsium.simulation.simulator

    import cellsium.simulation.placement.base
    # import cellsium.simulation.placement.pybox2d
    import cellsium.simulation.placement.pymunk

    import cellsium.parameters
    import cellsium.random

    run_tests_recursively(cellsium)


if __name__ == '__main__':
    main()
