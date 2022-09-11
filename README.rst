.. If you read this on hub.docker.com, maybe visit the github page https://github.com/modsim/cellsium

CellSium Readme
===============

.. image:: https://img.shields.io/pypi/v/cellsium.svg
   :target: https://pypi.python.org/pypi/cellsium

.. image:: https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat
   :target: https://cellsium.readthedocs.io/en/latest/

.. image:: https://github.com/modsim/CellSium/actions/workflows/python-test.yml/badge.svg
   :target: https://github.com/modsim/CellSium/actions/workflows/python-test.yml

.. image:: https://codecov.io/gh/modsim/CellSium/branch/main/graph/badge.svg?token=L36RQXYBW7
    :target: https://codecov.io/gh/modsim/CellSium

.. image:: https://img.shields.io/badge/Docker-image-green?logo=docker
   :target: https://github.com/modsim/CellSium/pkgs/container/cellsium

.. image:: https://img.shields.io/pypi/l/cellsium.svg
   :target: https://opensource.org/licenses/BSD-2-Clause

CellSium - *Cell* *Si*\ mulator for *micro*\ fluidic *m*\ icrocolonies

.. figure:: https://raw.githubusercontent.com/modsim/CellSium/animation/output.gif
    :align: center

    CellSium example simulation result


Front Matter
------------

CellSium is a cell simulator developed for the primary application of generating realistically looking images of bacterial microcolonies, which may serve as ground truth for machine learning training processes.

Publication
###########

If you use CellSium within scientific research, we ask you to cite our publication:

    Sachs CC, Ruzaeva K, Seiffarth J, Wiechert W, Berkels B, Nöh K (2022)
    CellSium: versatile cell simulator for microcolony ground truth generation
    Bioinformatics Advances, Volume 2, Issue 1, 2022, vbac053, doi: 10.1093/bioadv/vbac053

It is available on the *Bioinformatics Advances* homepage at `DOI: 10.1093/bioadv/vbac053 <https://doi.org/10.1093/bioadv/vbac053>`.

Documentation
#############

The documentation to CellSium can be built using `Sphinx <https://www.sphinx-doc.org/>`_, or be found readily built at `Read the Docs <https://cellsium.readthedocs.io/en/latest/>`_.

License
#######

CellSium is available under the :doc:`BSD license <license>`.

Installation
------------

Installation using pip
######################

CellSium can be installed via pip, ideally create and activate an environment beforehand to install CellSium in.

.. code-block:: bash

    > python -m pip install cellsium

Installation using conda
########################

CellSium is available in the modsim Anaconda channel as well, using packages from the conda-forge channel. It can be
installed with the following commands:

.. code-block:: bash

    > conda install -c modsim -c conda-forge -y cellsium

Usage
-----

Once installed, run CellSium via :code:`python -m cellsium`, specifying the desired entrypoint and options, such as outputs.
CellSium is built modular, various output modules can be activated simultaneously. To get an overview of the available options,
use the :code:`--help` switch. Furthermore, the main mode of setting tunable parameters are so called *tunables*, which can
be set from the command line using the :code:`-t` switches. A list of tunables can be shown using the :code:`--tunables-show` argument.

.. code-block:: bash

    > python -m cellsium --help
    usage: __main__.py [-v] [-q] [-c CELL] [-p] [-w] [-o OUTPUT] [-h] [-m MODULE]
                   [--Output {COCOOutput,CsvOutput,FluorescenceRenderer,GenericMaskOutput,JsonPickleSerializer,MeshOutput,NoisyUnevenIlluminationPhaseContrast,PhaseContrastRenderer,PlainRenderer,PlotRenderer,QuickAndDirtyTableDumper,SvgRenderer,TiffOutput,TrackMateXML,UnevenIlluminationPhaseContrast,YOLOOutput}]
                   [--PlacementSimulation {Box2D,Chipmunk,NoPlacement}] [-t TUNABLE] [--tunables-show] [--tunables-load TUNABLES_LOAD] [--tunables-save TUNABLES_SAVE]

    optional arguments:
      -h, --help            show this help message and exit
      -o OUTPUT, --output-file OUTPUT
      -w, --overwrite
      -p, --prefix
      -c CELL, --cell CELL
      -q, --quiet
      -v, --verbose
      -m MODULE, --module MODULE
      --Output {COCOOutput,CsvOutput,FluorescenceRenderer,GenericMaskOutput,JsonPickleSerializer,MeshOutput,NoisyUnevenIlluminationPhaseContrast,PhaseContrastRenderer,PlainRenderer,PlotRenderer,QuickAndDirtyTableDumper,SvgRenderer,TiffOutput,TrackMateXML,UnevenIlluminationPhaseContrast,YOLOOutput}
      --PlacementSimulation {Box2D,Chipmunk,NoPlacement}
      -t TUNABLE, --tunable TUNABLE
      --tunables-show
      --tunables-load TUNABLES_LOAD
      --tunables-save TUNABLES_SAVE


You can for example run a default simulation by just starting CellSium, the results will be shown interactively using matplotlib:

.. code-block:: bash

    > python -m cellsium

For more in-depth usage examples, please see the :doc:`examples <examples>` section.

Docker
------

An alternative to installing CellSium locally is running it via Docker. To run CellSium without interactive (GUI) elements, the following Docker command can be used, with parameters to CellSium being appended.

.. code-block:: bash

    > docker run --tty --interactive --rm --volume `pwd`:/data --user `id -u` ghcr.io/modsim/cellsium

To use interactive (GUI) elements such as the :code:`PlotRenderer`, an X server must be reachable; under Linux the following command can be used:

.. code-block:: bash

    > docker run --tty --interactive --rm --volume `pwd`:/data --user `id -u` --env DISPLAY=$DISPLAY --volume /tmp/.X11-unix:/tmp/.X11-unix ghcr.io/modsim/cellsium
