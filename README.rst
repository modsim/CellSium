.. If you read this on hub.docker.com, maybe visit the github page https://github.com/modsim/cellsium

CellSium Readme
===============

.. image:: https://img.shields.io/pypi/v/cellsium.svg
   :target: https://pypi.python.org/pypi/cellsium

.. image:: https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat
   :target: https://cellsium.readthedocs.io/en/latest/

.. image:: https://api.travis-ci.com/modsim/CellSium.svg?branch=main
   :target: https://app.travis-ci.com/github/modsim/CellSium

.. image:: https://codecov.io/gh/modsim/CellSium/branch/main/graph/badge.svg?token=L36RQXYBW7
    :target: https://codecov.io/gh/modsim/CellSium

.. image:: https://img.shields.io/docker/build/modsim/cellsium.svg
   :target: https://hub.docker.com/r/modsim/cellsium

.. image:: https://img.shields.io/pypi/l/cellsium.svg
   :target: https://opensource.org/licenses/BSD-2-Clause

CellSium - *Cell* *Si*\ mulator for *micro*\ fluidic *m*\ icrocolonies

Front Matter
------------

CellSium is a cell simulator developed for the primary application of generating realistically looking images of bacterial microcolonies, which may serve as ground truth for machine learning training processes.

Publication
###########

The publication is currently in preparation. If you use CellSium within scientific research, we ask you to cite our publication.

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

    > python -m pip install cellsium opencv-python

Installation using conda
########################

CellSium is available in the modsim Anaconda channel as well, using packages from the conda-forge channel. It can be
installed with the following commands:

.. code-block:: bash

    > conda install -c modsim -c conda-forge -y cellsium

Usage
-----

Once installed, run CellSium via :code:`python -m cellsium`, specifying the desired entrypoint and options, such as outputs.
CellSium is built modular, various output modules can be activated simultaneously:

.. code-block:: bash

    > python -m cellsium --help



You can for example run a default simulation by just starting CellSium, the results will be shown interactively using matplotlib:

.. code-block:: bash

    > python -m cellsium

Various output modes can be activated, some however only support writing their outputs to disk.

.. code-block:: bash

    > python -m cellsium --Output
