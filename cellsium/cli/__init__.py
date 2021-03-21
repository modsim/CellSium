from pathlib import Path

from ..model import PlacedCell, SizerCell
from ..simulation.placement import PlacementSimulation
from ..simulation.simulator import Simulator

# class Cell(PlacedCell, TimerCell):
#     pass


class Cell(PlacedCell, SizerCell):
    pass


def initialize_simulator():
    simulator = Simulator()
    ps = PlacementSimulation()

    simulator.sub_simulators += [ps]

    return simulator


def initialize_cells(simulator, count=0, cell_type=None, sequence=None):
    if cell_type is None:
        cell_type = Cell

    random_sequences = cell_type.get_random_sequences(sequence=sequence)

    for _ in range(count):

        init_kwargs = {k: next(v) for k, v in random_sequences.items()}

        # handling for items which are generated jointly,
        # but need to go to separate kwargs
        for k, v in list(init_kwargs.items()):
            if '__' in k:
                del init_kwargs[k]
                k_fragments = k.split('__')
                for inner_k, inner_v in zip(k_fragments, v):
                    init_kwargs[inner_k] = inner_v

        cell = cell_type(**init_kwargs)
        cell.birth()
        simulator.add(cell)


def add_output_prefix(output_name, output=None):
    output_name = Path(output_name)

    output_name = output_name.parent / (
        output.__class__.__name__ + '-' + output_name.name
    )

    return str(output_name)
