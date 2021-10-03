import importlib
import sys
import types
import warnings
from runpy import run_module

import matplotlib.pyplot
import pytest

from ..cli.simulate import SimulationDuration
from ..random import RRF


def test_random_generator(reset_state):
    fun = RRF.generator.integers(0, 1)
    assert fun() == 0


def test_random_sequence(reset_state):
    seq = RRF.sequence.integers(0, 1)
    assert next(seq) == 0


def test_test_launcher(reset_state, mock_sys_argv):
    with mock_sys_argv(['mock']):
        with pytest.raises(SystemExit):
            run_module('cellsium.tests', run_name='__main__')


def test_launcher(reset_state, mock_sys_argv):
    with mock_sys_argv(['mock', '--help']):
        with pytest.raises(SystemExit):
            run_module('cellsium', run_name='__main__')


def test_launcher_raw(reset_state, mock_sys_argv, tunables, monkeypatch, nop):

    monkeypatch.setattr(matplotlib.pyplot, 'ion', nop)
    monkeypatch.setattr(matplotlib.pyplot, 'show', nop)

    with mock_sys_argv(['mock']):
        with tunables((SimulationDuration, 1.0)):
            with pytest.raises(SystemExit):
                run_module('cellsium', run_name='__main__')


@pytest.mark.parametrize(
    'add_filename,arg',
    [
        (False, None),
        (True, None),
        (True, 'LWPOLYLINE'),
        (True, 'POLYLINE'),
        (True, 'SPLINE'),
    ],
)
def test_dxf_gen(add_filename, arg, tmpdir, mock_sys_argv):

    output_name = tmpdir.join('test.dxf')

    argv = ['mock']
    if add_filename:
        argv.append(str(output_name))
    if arg:
        argv.append(arg)

    with mock_sys_argv(argv):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            run_module('cellsium.tests.generate_dxf_file', run_name='__main__')

    if add_filename:
        assert output_name.isfile()


def test_missing_box2d(
    patch_sys_modules, fix_dynamic_module_reloading_subclass_problems
):
    with fix_dynamic_module_reloading_subclass_problems():
        with patch_sys_modules(remove=['cellsium.simulation.placement*', 'Box2D*']):
            sys.modules['Box2D'] = None
            importlib.import_module('cellsium.simulation.placement')


def test_old_pymunk_mock(
    patch_sys_modules, fix_dynamic_module_reloading_subclass_problems
):
    mock_module = types.ModuleType('pymunkoptions', 'Just a mock pymunkoptions module')
    mock_module.__dict__['options'] = dict()

    with fix_dynamic_module_reloading_subclass_problems():
        with patch_sys_modules(remove=['cellsium.simulation.placement*', 'pymunk*']):
            sys.modules[mock_module.__name__] = mock_module
            importlib.import_module('cellsium.simulation.placement')


def test_patch_sys_modules(patch_sys_modules):
    with patch_sys_modules(remove=None):
        sys.modules['some_non_existing_lib'] = None


def test_instantiate_protocols():
    # function to get the lines covered
    from ..typing import AnyFunction, KwargFunction

    def nop(self, *args, **kwargs):
        pass

    AnyFunction.__init__ = nop
    AnyFunction()(None)

    KwargFunction.__init__ = nop
    KwargFunction()(None, dummy=None)
