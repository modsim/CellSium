import pytest

from ..cli.cli import main
from ..output import Output
from ..simulation.placement.base import PlacementSimulationSimplification

ALL_OUTPUTS = [
    'COCOOutput',
    'FluorescenceRenderer',
    'GenericMaskOutput',
    'JsonPickleSerializer',
    'MeshOutput',
    'NoisyUnevenIlluminationPhaseContrast',
    'PhaseContrastRenderer',
    'PlainRenderer',
    'PlotRenderer',
    'QuickAndDirtyTableDumper',
    'SvgRenderer',
    'TiffOutput',
    'TrackMateXML',
    'UnevenIlluminationPhaseContrast',
    'YOLOOutput',
]


def _generate_tunables(t):
    args = []
    if t:
        for k, v in t.items():
            args.append('-t')
            args.append('%s=%s' % (k, v))
    return args


def _generate_output(Output):
    args = []
    if Output:
        for an_output in Output:
            args.append('--Output')
            args.append(an_output)
    return args


def generate_commandline(
    task='training',
    prefix=False,
    overwrite=False,
    verbose=False,
    quiet=False,
    t=None,
    output=None,
    Output=None,
    PlacementSimulation=None,
    args=None,
):
    if args is None:
        additional_args = []
    else:
        additional_args = args

    args = [task]
    if prefix:
        args.append('--prefix')

    if overwrite:
        args.append('--overwrite')

    if verbose:
        args.append('--verbose')

    if quiet:
        args.append('--quiet')

    args += _generate_tunables(t)

    if output:
        args.append('--output')
        args.append(output)

    args += _generate_output(Output)

    if PlacementSimulation:
        args.append('--PlacementSimulation')
        args.append(PlacementSimulation)

    args += additional_args

    return args


def call_main(*args, **kwargs):
    args = generate_commandline(*args, **kwargs)

    return_value = main(args)

    assert return_value is None or return_value == 0


def test_training_outputs(reset_state, tmpdir):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'training',
        prefix=True,
        overwrite=True,
        t=dict(TrainingDataCount=2, TrainingImageWidth=64, TrainingImageHeight=64),
        output=str(output_dir) + '/output_name',
        Output=ALL_OUTPUTS,
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0


def test_quiet_switch(reset_state, tmpdir):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'training',
        quiet=True,
        t=dict(TrainingDataCount=2),
        output=str(output_dir) + '/output_name',
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0


def test_verbose_switch(reset_state, tmpdir):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'training',
        verbose=True,
        t=dict(TrainingDataCount=2),
        output=str(output_dir) + '/output_name',
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0


def test_debug_switch(reset_state, tmpdir):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'training',
        t=dict(TrainingDataCount=2),
        output=str(output_dir) + '/output_name',
        args=['-vv'],
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0


def test_training_no_output_set(reset_state):
    with pytest.raises(RuntimeError):
        call_main('training', t=dict(TrainingDataCount=2), Output=ALL_OUTPUTS)


def test_simulation_output_no_prefix(reset_state, tmpdir):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'simulate',
        overwrite=True,
        t=dict(
            SimulationTimestep=0.1, SimulationOutputInterval=0.1, SimulationDuration=0.2
        ),
        output=str(output_dir) + '/output_name',
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0


def test_simulation_outputs(reset_state, tmpdir):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'simulate',
        prefix=True,
        overwrite=True,
        t=dict(
            SimulationTimestep=0.1,
            SimulationOutputInterval=0.1,
            SimulationDuration=0.2,
            SimulationOutputFirstState=1,
            Width=10,
            Height=10,
        ),
        output=str(output_dir) + '/output_name',
        Output=ALL_OUTPUTS,
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0


@pytest.mark.parametrize('s', [2, 1])
def test_simulation_placementsimplification(s, reset_state, tmpdir):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'simulate',
        prefix=True,
        overwrite=True,
        t=dict(
            SimulationTimestep=0.1,
            SimulationOutputInterval=0.1,
            SimulationDuration=0.2,
            PlacementSimulationSimplification=s,
        ),
        output=str(output_dir) + '/output_name',
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0


class InterruptOutput(Output):
    interrupt_at = 0

    def __init__(self):
        self.round = 0

    #     def display(self, world, **kwargs):
    #         self.output(world, **kwargs)

    def write(self, world, file_name, **kwargs):
        self.output(world, **kwargs)

    def output(self, world, **kwargs):
        if self.__class__.interrupt_at == self.round:
            raise KeyboardInterrupt
        self.round += 1


@pytest.mark.parametrize('interrupt_at', [0, 1])
def test_simulation_keyboard_interrupt(interrupt_at, reset_state, tmpdir):
    # this test is somewhat slow, but quite important to check whether all
    # outputs handle deallocation properly
    # (either before or after they had something to do)
    output_dir = tmpdir.mkdir('result')

    InterruptOutput.interrupt_at = interrupt_at

    call_main(
        'simulate',
        prefix=True,
        overwrite=True,
        t=dict(
            SimulationTimestep=0.1,
            SimulationOutputInterval=0.1,
            SimulationDuration=-1,
            Width=10,
            Height=10,
        ),
        output=str(output_dir) + '/output_name',
        Output=['InterruptOutput'] + ALL_OUTPUTS,
    )

    generated_files = output_dir.listdir()

    print(generated_files)

    if interrupt_at == 0:
        assert len(generated_files) == 0
    else:
        assert len(generated_files) > 0


@pytest.mark.parametrize('dxftype', ['LWPOLYLINE'])
def test_simulation_outputs_with_boundary(dxftype, reset_state, tmpdir, dxf_file):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'simulate',
        prefix=True,
        overwrite=True,
        t=dict(
            SimulationTimestep=0.1,
            SimulationOutputInterval=0.1,
            SimulationDuration=0.2,
            BoundariesFile=str(dxf_file(dxftype)),
            Width=20,
            Height=20,
        ),
        output=str(output_dir) + '/output_name',
        Output=ALL_OUTPUTS,
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0


@pytest.mark.parametrize('dxftype', ['LWPOLYLINE', 'POLYLINE', 'SPLINE'])
def test_simulation_with_boundary(dxftype, reset_state, tmpdir, dxf_file):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'simulate',
        prefix=True,
        overwrite=True,
        t=dict(
            SimulationTimestep=0.1,
            SimulationOutputInterval=0.1,
            SimulationDuration=0.2,
            BoundariesFile=str(dxf_file(dxftype)),
        ),
        output=str(output_dir) + '/output_name',
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0


@pytest.mark.parametrize('dxftype', ['LWPOLYLINE'])
def test_simulation_with_boundary_box2d(dxftype, reset_state, tmpdir, dxf_file):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'simulate',
        prefix=True,
        overwrite=True,
        t=dict(
            SimulationTimestep=0.1,
            SimulationOutputInterval=0.1,
            SimulationDuration=0.2,
            BoundariesFile=str(dxf_file(dxftype)),
            PlacementSimulationSimplification=2,
        ),
        PlacementSimulation='Box2D',
        output=str(output_dir) + '/output_name',
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0


def test_render(reset_state, tmpdir):
    output_dir = tmpdir.mkdir('result')

    call_main(
        'training',
        overwrite=True,
        t=dict(TrainingDataCount=1),
        output=str(output_dir) + '/output_name',
        Output=['JsonPickleSerializer'],
    )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0

    reset_state()

    output_dir_2 = tmpdir.mkdir('result2')

    call_main(
        'render',
        output=str(output_dir_2) + '/output_name',
        Output=['GenericMaskOutput'],
        args=['--input-file', str(output_dir) + '/output_name000.json'],
    )

    generated_files = output_dir_2.listdir()

    assert len(generated_files) > 0


@pytest.mark.parametrize('s', [2, 1])
def test_training_box2d_placementsimplification(s, reset_state, tmpdir, tunables):
    output_dir = tmpdir.mkdir('result')

    with tunables((PlacementSimulationSimplification, s)):
        call_main(
            'simulate',
            prefix=True,
            overwrite=True,
            PlacementSimulation='Box2D',
            t=dict(
                SimulationTimestep=0.1,
                SimulationOutputInterval=0.1,
                SimulationDuration=0.2,
                PlacementSimulationSimplification=s,
            ),
            output=str(output_dir) + '/output_name',
        )

    generated_files = output_dir.listdir()

    assert len(generated_files) > 0
