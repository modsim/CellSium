# CellSium

CellSium - *Cell* *Si*mulator for *micro*fluidic *m*icrocolonies

This software is currently in development. Install process is not smoothed out yet, and may require manual interventions.

- Clone the repository and run `pip install . --user` (possibly `pip3`)
- OpenCV is likely not installable via pip, install it either via system tools, or e.g. anaconda.
  <br />If `pip` doesn't find the installed OpenCV, uncomment the opencv requirement line in `setup.py` before proceeding.
- CellSium needs a currently pre-release `tunable` version, install via `pip install https://github.com/csachs/tunable/archive/master.zip --user`
- CellSium needs currently not in PyPI package imagej-tiff-meta (for ImageJ-compatible ROI writing), install via `pip install https://github.com/csachs/imagej-tiff-meta/archive/master.zip --user`

```
# run as runnable python module:

python -m cellsium -t tunable=value --Output OutputModuleA --Output OutputModuleB ...
```
