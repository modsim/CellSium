# CellSium

CellSium - *Cell* *Si*mulator for *micro*fluidic *m*icrocolonies

This software is currently in development. Install process:

- `conda build recipe`
- `conda create -n cellsium`
- `conda activate cellsium`
- `conda install -c local cellsium`


```
# run as runnable python module:

python -m cellsium
# python -m cellsium -t tunable=value --Output OutputModuleA --Output OutputModuleB ...

# show all tunables 
python -m cellsium --tunables-show

# run a simulation, get cells
python -m cellsium --Output TiffOutput -o result.tif -t SimulationDuration=6

# run a different simulation

python -m cellsium --Output TiffOutput -o result_seed2.tif -t SimulationDuration=6 -t Seed=2

# just produce randomly placed cells as training data

python -m cellsium.cli.training -o output.tif

# ... with some more parameters

python -m cellsium.cli.training -o output.tif -t TrainingDataCount=128 -t TrainingCellCount=64 -t TrainingImageWidth=512 -t TrainingImageHeight=512

```
