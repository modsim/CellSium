"""
The tests modules contains a doctests launcher.
"""

import doctest
from types import ModuleType


def collect_modules_recursive(start, blacklist=None):
    """
    Collects all modules and submodules in a recursive manner.

    :param start: the top module to start from
    :param blacklist: a string or list of strings of module
        (sub)names which should be ignored.
    :return:
    """

    if blacklist is None:
        blacklist = []
    elif not isinstance(blacklist, list):
        blacklist = [blacklist]

    collector = set()

    def _inner(current):
        if current in collector or current.__name__ in blacklist:
            return

        collector.add(current)

        for another in dir(current):
            another = getattr(current, another)
            if isinstance(another, ModuleType):
                if another.__name__.startswith(start.__name__):
                    _inner(another)

    _inner(start)

    return list(sorted(collector, key=lambda module: module.__name__))


def run_tests_recursively(start_module, blacklist=None, quiet=False):
    """
    Runs doctests recursively.

    :param start_module: the top module to start from
    :param blacklist: a string or list of strings of module
        (sub)names which should be ignored.
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

    return total_failures


# noinspection PyUnresolvedReferences
def run_doctests(quiet=False):
    """
    Runs all the doctests.

    """

    import cellsium.cli.cli
    import cellsium.cli.render
    import cellsium.cli.training
    import cellsium.geometry
    import cellsium.model
    import cellsium.model.agent
    import cellsium.model.geometry
    import cellsium.output
    import cellsium.output.all
    import cellsium.parameters
    import cellsium.random
    import cellsium.simulation
    import cellsium.simulation.placement.base
    import cellsium.simulation.placement.pybox2d
    import cellsium.simulation.placement.pymunk
    import cellsium.simulation.simulator

    return run_tests_recursively(cellsium, quiet=quiet)


def main():
    return run_doctests()
