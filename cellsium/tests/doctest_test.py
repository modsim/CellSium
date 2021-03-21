import sys
import types

import cellsium

from . import collect_modules_recursive, run_tests_recursively


def test_doctest():
    # chain run
    from . import run_doctests

    assert run_doctests(quiet=True) == 0


def test_doctest_cmr_str():
    result = collect_modules_recursive(cellsium, blacklist='cellsium')
    assert result == []


def test_doctest_cmr_list():
    result = collect_modules_recursive(cellsium, blacklist=['cellsium'])
    assert result == []


def test_doctest_fail_a_test(patch_sys_modules):
    def a_test_function():
        """
        Fail a doctest.

        >>> a_test_function()
        43
        """
        return 42

    mock_module = types.ModuleType('MockModule', 'Just a mock module')
    mock_module.__dict__['a_test_function'] = a_test_function
    a_test_function.__module__ = mock_module.__name__

    with patch_sys_modules():
        sys.modules[mock_module.__name__] = mock_module
        assert run_tests_recursively(mock_module) == 1
