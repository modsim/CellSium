# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Build like:
# sphinx-build -b html docs docs/_build

# -- Path setup --------------------------------------------------------------


import os
import sys

assert sys.version_info.major == 3
if sys.version_info.minor < 8:
    # readthedocs runs Python 3.7
    import typing

    class Protocol:
        pass

    typing.Protocol = Protocol

sys.path.insert(0, os.path.abspath('..'))

import cellsium  # noqa

try:
    import sphinx_rtd_theme
except ImportError:
    sphinx_rtd_theme = None

# -- Project information -----------------------------------------------------

project = cellsium.__name__
copyright = cellsium.__copyright__
author = cellsium.__author__
release = cellsium.__version__


# -- General configuration ---------------------------------------------------

sys.path.insert(0, os.path.abspath('./_ext'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'automagicdoc',
]

automagic_modules = [cellsium]
automagic_ignore = ['*test*', 'cellsium.output.all']


language = 'en'

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


if sphinx_rtd_theme:
    extensions.append('sphinx_rtd_theme')
    html_theme = 'sphinx_rtd_theme'
