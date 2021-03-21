from cellsium.simulation import BaseSimulator
from cellsium.simulation.placement import Chipmunk
from cellsium.simulation.simulator import Simulator, Timestep


def test_simulator_empty(simulator):
    for cell in simulator.simulation.world.cells:
        simulator.simulation.world.remove(cell)

    simulator.simulation.world.commit()

    simulator.step(60.0)

    assert len(simulator.simulation.world.cells) == 0


def test_simulator_clear(simulator):
    simulator.step(60.0)

    assert len(simulator.simulation.world.cells) == 1

    simulator.clear()

    assert len(simulator.simulation.world.cells) == 0


def test_simulator_basic(simulator):
    simulator.step(60.0)

    assert len(simulator.simulation.world.cells) == 1


def test_simulator_division(simulator):
    for _ in range(1):
        simulator.step(60.0 * 60.0)

    assert len(simulator.simulation.world.cells) == 2


def test_simulator_timestep():
    s = Simulator()
    half_an_hour = 30.0 * 60.0
    s.simulation.time = half_an_hour
    ts = Timestep(half_an_hour, s.simulation, s)

    assert ts.time_hours == 0.5


def test_simulator_basesimulator_class():
    bs = BaseSimulator()

    bs.add(None)
    bs.remove(None)
    bs.add_boundary(None)
    bs.clear()
    bs.step(None)


def test_chipmunk_rare_code_paths(simulator):
    # five generations
    for t in range(5):
        ts = Timestep(t, simulator.simulation, simulator)
        for cell in simulator.simulation.world.cells:
            cell.divide(ts)
        simulator.simulation.world.commit()

    phys = Chipmunk()

    phys.verbose = True

    simulator.sub_simulators.append(phys)

    for _ in range(5):
        simulator.step(60.0)

    phys.look_back_threshold = 0

    for _ in range(5):
        simulator.step(60.0)

    phys.inner_step(time_step=0.1, iterations=5, converge=False)
