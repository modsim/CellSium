from ..cli import Cell, initialize_cells
from ..model import BentRod, PlacedCell, SimulatedCell, TimerCell, WithFluorescence
from ..model.initialization import RandomFluorescence
from ..simulation.placement import Chipmunk
from ..simulation.placement.base import PlacementSimulationSimplification


def test_cell_repr(simulator):
    cell = simulator.simulation.world.cells[0]

    cell_repr = repr(cell)

    expected_cell_repr = (
        'Cell(angle=3.6942842669518385, bend_lower=-0.09614075306364522, '
        'bend_overall=0.01753978255362451, bend_upper=-0.04126808565523994, '
        'birth_time=0.0, division_size=2.898390206023354, elongation_rate=1.5, '
        'id_=1, length=1.636246698756115, lineage_history=[0], parent_id=0, '
        'position=[17.90727229572483, 29.944407189601154], width=0.9548930351446809)'
    )

    assert cell_repr == expected_cell_repr


def test_fluorescent_cell(simulator):
    class AFluorescentCell(WithFluorescence, RandomFluorescence, Cell):
        pass

    initialize_cells(simulator, count=1, cell_type=AFluorescentCell)

    simulator.simulation.world.commit()

    assert isinstance(simulator.simulation.world.cells[-1], AFluorescentCell)


def test_timer_cell(simulator):
    class ATimerCell(PlacedCell, TimerCell):
        pass

    initialize_cells(simulator, count=1, cell_type=ATimerCell)

    simulator.simulation.world.commit()

    assert isinstance(simulator.simulation.world.cells[-1], ATimerCell)

    for _ in range(2):
        simulator.step(60.0 * 60.0)


def test_simulatedcell_dummy():
    cell = SimulatedCell()
    cell.birth()
    cell.grow(1.0)


def test_cell_zoo(simulator, tunables, add_cell_zoo):
    add_cell_zoo(simulator)

    simulator.sub_simulators.append(Chipmunk())

    simulator.step(60.0)

    with tunables((PlacementSimulationSimplification, 1)):
        simulator.step(60.0)

    with tunables((PlacementSimulationSimplification, 2)):
        simulator.step(60.0)


def test_cell_bentrod_call_unused_meshfunction(simulator):
    cell = simulator.simulation.world.cells[0]
    BentRod.raw_points3d(cell)
