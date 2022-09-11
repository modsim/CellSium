Examples
========

The following sections contain some usage examples of CellSium.

Creating random training data
#############################

The core mode of operation is the creation of ground truth data as training data for machine learning/deep learning applications. To this end, CellSium contains two output modes specifically tailored to produce outputs for common deep learning based object detectors/instance segmentation toolkits: The COCO and YOLO format. CellSium can as well just output binary masks along the images for use with other learning tools.

For example, the following command will random cell images, and output three datasets:

.. code-block:: bash

    > python -m cellsium training \
        -t TrainingDataCount=64 \
        -t TrainingCellCount=512 \
        -t TrainingImageWidth=512 \
        -t TrainingImageHeight=512 \
        -t Calibration=0.0905158 \
        -t ChipmunkPlacementRadius=0.01 \
        -o training \
        --Output COCOOutput \
        --Output YOLOOutput \
        --Output GenericMaskOutput \
        -p

Note how the main mode of configuration of CellSium are *tunables*, these tunable parameters are set using the :code:`-t` argument, followed by :code:`Name=value`. The tunables are explained in the documentation, and can be listed via :code:`--tunables-show` as well.

In this example, the output of 64 images of 512x512 size are requested, setting the pixel calibration to 0.0905158 µm per pixel. :code:`ChipmunkPlacementRadius` configures the physical placement and yields denser colonies. The name of the output files/directories is specified using :code:`-o`.

The outputs of CellSium are modular. In this example, the :code:`COCOOutput`, :code:`YOLOOutput`, and :code:`GenericMaskOutput` are enabled. As to prevent name clashes and allow easy coexistence, the :code:`-p:code:` switch enables prefixing of the output names with the name of the respective output module.

Once the exmaple has run, the directories :code:`COCOOutput-training`, :code:`GenericMaskOutput-training`, and :code:`YOLOOutput-training` have been created, with examples of the :code:`GenericMaskOutput` shown.

.. list-table::

    * - .. figure:: _static/GenericMaskOutput-training/images/000000000000.png
          :width: 256

          :code:`GenericMaskOutput-training/images/000000000000.png`

      - .. figure:: _static/GenericMaskOutput-training/masks/000000000000.png
          :width: 256

          :code:`GenericMaskOutput-training/masks/000000000000.png`

Creating a timelapse simulation
###############################

CellSium was originally developed to create time lapse simulations to create realistic microcolonies, which can serve as input data e.g., for simulations based on the geometry or the training and validation of tracking algorithms.
To run a simulation, ste up the desired outputs and tunables as explained, and use the :code:`simulate` subcommand.

.. code-block:: bash

    > python -m cellsium simulate \
        -o simulate \
        --Output GenericMaskOutput \
        --Output TiffOutput \
        -p

In this case, a microcolony will be simulated, a time lapse TIFF stack as well as mask output generated. Shown are three example images:

.. list-table::

    * - .. figure:: _static/GenericMaskOutput-simulate/images/000000000000.png
          :width: 256

          :code:`GenericMaskOutput-training/images/000000000000.png`

    * - .. figure:: _static/GenericMaskOutput-simulate/images/000000000016.png
          :width: 256

          :code:`GenericMaskOutput-training/images/000000000016.png`

    * - .. figure:: _static/GenericMaskOutput-simulate/images/000000000032.png
          :width: 256

          :code:`GenericMaskOutput-training/images/000000000032.png`

Adding a custom cell model
##########################

In the previous examples, the standard (sizer) cell model was used. However, the modular nature of CellSium makes it easy to integrate a custom cell model. In this example, the sizer model will be defined externally, so it can be more easily changed, and to showcase its difference, the easter egg square geometry will be applied:

.. literalinclude:: square.py
    :caption: square.py

The custom model can be specified using the :code:`-c` switch, specifying either an importable Python module, or the path of a Python file. If no class name is specified after the :code:`:` colon, CellSium will attempt to import a class named :code:`Cell` from the file/module.

.. code-block:: bash

    > python -m cellsium simulate \
        -o square \
        --Output GenericMaskOutput \
        -c square.py:Cell \
        -p

CellSium cell objects are Python objects. They are built lending from OOP principles, using mixins in a very flexible way to join various properties. To gain deeper insights how to implement and alter cellular behavior or rendering, it is best to study the source code of CellSium.

.. list-table::

    * - .. figure:: _static/GenericMaskOutput-square/images/000000000033.png
          :width: 256

          :code:`GenericMaskOutput-square/images/000000000033.png`


.. include:: Embedding.rst
