# -*- coding: utf-8 -*-
"""
documentation
"""

from setuptools import setup, find_packages

import sys
sys.path.insert(0, '.')

import cellsium

setup(
    name='cellsium',
    version=cellsium.__version__,
    description='CellSium - _Cell_ _Si_mulator for _micro_fluidic _m_icrocolonies',
    long_description='see https://github.com/modsim/cellsium',
    author=cellsium.__author__,
    author_email='c.sachs@fz-juelich.de',
    url='https://github.com/modsim/cellsium',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'scipy',
        'matplotlib',
        'tunable',
        'jsonpickle',
        'tqdm',
        'pymunk',
        'opencv',
        'numpy-stl',
        'ezdxf'
    ],
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Image Recognition',
    ]
)
