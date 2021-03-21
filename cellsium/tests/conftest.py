import fnmatch
import gc
import os
import sys
from contextlib import contextmanager

import pytest
from tunable import Selectable, TunableManager

from ..cli import initialize_cells, initialize_simulator
from ..model import (
    BentRod,
    Coccoid,
    Ellipsoid,
    IdCounter,
    Rectangle,
    RodShaped,
    SizerCell,
    Square,
    WithFluorescence,
    generate_cell,
)
from ..model.initialization import RandomFluorescence
from ..random import RRF
from .generate_dxf_file import generate_dxf_file


@contextmanager
def _patch_sys_modules(remove=None):
    gc.collect()

    if remove is None:
        remove = []

    sys_modules_keys = set()
    sys_modules_extract = {}

    for key, value in sys.modules.items():
        for to_remove in remove:
            if fnmatch.fnmatch(key, to_remove):
                sys_modules_extract[key] = value

        sys_modules_keys.add(key)

    try:
        for key in sys_modules_extract.keys():
            del sys.modules[key]

        yield

    finally:
        new_sys_modules_keys = set(sys.modules.keys())
        difference = new_sys_modules_keys - sys_modules_keys

        for key in difference:
            del sys.modules[key]

        # important for proper cleanup
        for key in sys_modules_extract.keys():
            if key in sys.modules:
                del sys.modules[key]

        gc.collect()

        for key, value in sys_modules_extract.items():
            sys.modules[key] = value


@pytest.fixture
def patch_sys_modules():
    return _patch_sys_modules


def get_recursive_subclasses(class_):
    def collect(inner_class, collector=set(), skip=None):
        if inner_class != skip:
            collector.add(inner_class)
        for iter_class in inner_class.__subclasses__():
            collect(iter_class)
        return collector

    return collect(class_, skip=class_)


def fix_bases(base_class, pattern='*', keep=None):
    for item in get_recursive_subclasses(base_class):
        if keep and item in keep:
            continue
        if fnmatch.fnmatch(item.__name__, pattern):
            new_bases = tuple([base for base in item.__bases__ if base != base_class])
            # if not new_bases:
            #     new_bases = (object,)

            item.__bases__ = new_bases


@contextmanager
def _fix_dynamic_module_reloading_subclass_problems():
    keep_selectable = get_recursive_subclasses(Selectable)
    # keep_tunable = get_recursive_subclasses(Tunable)

    try:
        yield
    finally:
        fix_bases(Selectable, '*', keep=keep_selectable)
        # fix_bases(Tunable, '*', keep=keep_tunable)
        gc.collect()


@pytest.fixture
def fix_dynamic_module_reloading_subclass_problems():
    return _fix_dynamic_module_reloading_subclass_problems


@contextmanager
def _mock_sys_argv(new_value):
    argv = sys.argv
    try:
        sys.argv = new_value
        yield
    finally:
        sys.argv = argv


@pytest.fixture
def mock_sys_argv():
    return _mock_sys_argv


def perform_reset_state():
    # we have implicit state in CellSium in three places ...

    # ... the tunables / selectables

    TunableManager.init()

    Selectable.SelectableChoice.overrides.clear()
    Selectable.SelectableChoice.parameters.clear()

    # ... the random number generator

    RRF.seed(1)

    # ... the id counter to assign globally unique ids to cells

    IdCounter.reset()


@pytest.fixture
def reset_state():
    perform_reset_state()

    return perform_reset_state


@pytest.fixture
def simulator(reset_state):
    simulator = initialize_simulator()

    initialize_cells(simulator, count=1, sequence=RRF.sequence)

    simulator.simulation.world.commit()

    return simulator


@pytest.fixture
def add_cell_zoo():
    def _inner(simulator):

        cell_types = [
            BentRod,
            RodShaped,
            Coccoid,
            Ellipsoid,
            Square,
            Rectangle,
            (BentRod, WithFluorescence, RandomFluorescence),
        ]

        for cell_type in cell_types:
            if not isinstance(cell_type, tuple):
                cell_type = (cell_type,)

            cell_type += (SizerCell,)

            generated_cell_type = generate_cell(
                *cell_type, name='Placed' + cell_type[0].__name__
            )

            initialize_cells(simulator, count=1, cell_type=generated_cell_type)

        simulator.simulation.world.commit()

    return _inner


@pytest.fixture
def dxf_file(tmpdir):
    location = tmpdir.join('test.dxf')

    def _callable(line_type):
        generate_dxf_file(str(location), line_type=line_type)
        return location

    return _callable


@contextmanager
def _tunables(*tunables_list):
    old_values = {}

    for t, v in tunables_list:
        old_values[t] = t.value

    try:
        for t, v in tunables_list:
            assert t.test(v)
            t.value = v

        yield

    finally:
        for t, v in tunables_list:
            t.value = old_values[t]
            t.reset()


@pytest.fixture
def tunables():
    return _tunables


@contextmanager
def _chdir(new_dir):
    cwd = os.getcwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(cwd)


@pytest.fixture
def chdir():
    return _chdir


@pytest.fixture
def nop(*args, **kwargs):
    def _nop(*args, **kwargs):
        pass

    return _nop
