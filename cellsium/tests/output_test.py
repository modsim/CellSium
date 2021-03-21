from pathlib import Path

import cv2
import matplotlib.pyplot
import numpy as np
import pytest
from numpy.testing import assert_almost_equal

from ..output import (
    OutputReproducibleFiles,
    check_overwrite,
    ensure_extension,
    ensure_path,
)
from ..output.all import (
    COCOOutput,
    FluorescenceRenderer,
    GenericMaskOutput,
    JsonPickleSerializer,
    MeshOutput,
    NoisyUnevenIlluminationPhaseContrast,
    Output,
    PlainRenderer,
    QuickAndDirtyTableDumper,
    SvgRenderer,
    TiffOutput,
    TrackMateXML,
    YOLOOutput,
)
from ..output.gt import (
    COCOEncodeRLE,
    COCOOutputStuff,
    GroundTruthOnlyCompleteCellsInImages,
    GroundTruthOutput,
    binary_to_rle,
)
from ..output.mesh import MeshCellScaleFactor
from ..output.plot import PlotRenderer
from ..output.render import (
    OpenCVimshow,
    RenderChannels,
    RoiOutputScaleDelta,
    RoiOutputScaleFactor,
    add_if_uneven,
    bytescale,
    cv2_has_write_support,
    get_canvas_points_for_cell,
    get_canvas_points_raw,
    new_canvas,
    render_on_canvas_matplotlib,
    scale_points_absolute,
    scale_points_relative,
)
from ..output.serialization import type2numpy
from ..output.xml import TrackMateXMLExportFluorescences, TrackMateXMLExportLengthTypo


def test_jsonpickle(simulator, capsys):

    output = JsonPickleSerializer()
    output.display(simulator.simulation.world)

    captured = capsys.readouterr()

    result = captured.out.replace('\n', '')
    expected = (
        '{"py/object": "cellsium.simulation.simulator.World", "cells": [{"py/object":'
        ' "cellsium.cli.Cell", "lineage_history": [0], "id_": 1, "parent_id": 0, '
        '"birth_time": 0.0, "angle": 3.6942842669518385, "position": '
        '[17.90727229572483, 29.944407189601154], "bend_overall": 0.01753978255362451,'
        ' "bend_upper": -0.04126808565523994, "bend_lower": -0.09614075306364522, '
        '"length": 1.636246698756115, "width": 0.9548930351446809, "division_size": '
        '2.898390206023354, "elongation_rate": 1.5}], "boundaries": [], '
        '"cells_to_add": [], "cells_to_remove": []}'
    )

    assert result == expected


def test_type2numpy_nomaxlen():
    assert type2numpy([1, 2]) == '(2,)i8'


def test_type2numpy_nonsense():
    with pytest.raises(RuntimeError):
        type2numpy(type2numpy)


def test_qadtd_empty(simulator):
    for cell in simulator.simulation.world.cells:
        simulator.simulation.world.remove(cell)

    simulator.simulation.world.commit()

    output = QuickAndDirtyTableDumper()

    assert len(output.output(simulator.simulation.world)) == 0


def test_svgrenderer_display(simulator):
    output = SvgRenderer()

    with pytest.raises(RuntimeError):
        output.display(simulator.simulation.world)


def test_trackmate_display(simulator):
    output = TrackMateXML()

    with pytest.raises(RuntimeError):
        output.display(simulator.simulation.world)


def test_trackmate_no_fluor(simulator, tunables, tmpdir):
    testfile = tmpdir.join('testfile.xml')
    for _ in range(2):
        simulator.step(60.0 * 60.0)

    with tunables((TrackMateXMLExportFluorescences, '')):
        output = TrackMateXML()

        output.write(simulator.simulation.world, testfile)


def test_trackmate_typo(simulator, tunables, tmpdir):
    testfile = tmpdir.join('testfile.xml')
    for _ in range(2):
        simulator.step(60.0 * 60.0)

    with tunables((TrackMateXMLExportLengthTypo, False)):
        output = TrackMateXML()

        output.write(simulator.simulation.world, testfile)


def test_trackmate_growth(simulator, tunables, tmpdir):
    testfile = tmpdir.join('testfile.xml')

    output = TrackMateXML()

    for _ in range(5):
        simulator.step(60.0 * 60.0)
        output.write(simulator.simulation.world, testfile, overwrite=True)


def test_gt_output(simulator):
    output = GroundTruthOutput()

    with pytest.raises(RuntimeError):
        output.output(simulator.simulation.world)


def test_gt_virtual():
    output = GroundTruthOutput()

    output._write_initializations(None, '')
    output._write_perform(None, '')


def test_yolo_off_canvas_cells(simulator, tmpdir, tunables):
    testdir = tmpdir.join('yoloout')

    output = YOLOOutput()

    simulator.step(60.0 * 60.0)

    # move one cell off canvas
    some_cell_position = simulator.simulation.world.cells[1].position
    some_cell_position[0] += 10000

    output.write(simulator.simulation.world, testdir)

    with tunables((GroundTruthOnlyCompleteCellsInImages, False)):
        output.write(simulator.simulation.world, testdir, overwrite=True)


def test_yolo_no_overwrite(simulator, tmpdir, tunables):
    with tunables((RenderChannels, 'PlainRenderer')):
        testdir = tmpdir.join('yoloout')

        output = YOLOOutput()

        output.write(simulator.simulation.world, testdir)

        output = YOLOOutput()

        with pytest.raises(RuntimeError):
            output.write(simulator.simulation.world, testdir)


def test_coco_no_overwrite(simulator, tmpdir, tunables):
    with tunables((RenderChannels, 'PlainRenderer')):

        testdir = tmpdir.join('cocoout')

        output = COCOOutput()
        output.write(simulator.simulation.world, testdir)

        output = COCOOutput()

        with pytest.raises(RuntimeError):
            output.write(simulator.simulation.world, testdir)


def test_coco_unreproducible_stuffthings(simulator, tmpdir, tunables):
    with tunables(
        (RenderChannels, 'PlainRenderer'),
        (OutputReproducibleFiles, False),
        (COCOOutputStuff, True),
        (COCOEncodeRLE, True),
    ):
        testdir = tmpdir.join('cocoout')

        output = COCOOutput()

        simulator.step(60.0 * 60.0)

        # move one cell off canvas
        some_cell_position = simulator.simulation.world.cells[1].position
        some_cell_position[0] += 10000

        output.write(simulator.simulation.world, testdir)

        with tunables((GroundTruthOnlyCompleteCellsInImages, False)):
            output.write(simulator.simulation.world, testdir, overwrite=True)


def test_genericmaskoutput_no_overwrite(simulator, tmpdir, tunables):
    with tunables((RenderChannels, 'PlainRenderer')):

        testdir = tmpdir.join('cocoout')

        output = GenericMaskOutput()

        output.write(simulator.simulation.world, testdir)

        output = GenericMaskOutput()

        with pytest.raises(RuntimeError):
            output.write(simulator.simulation.world, testdir)


def test_mesh_scale(reset_state, simulator, tmpdir, tunables):
    testfile = tmpdir.join('testfile.stl')

    with tunables((MeshCellScaleFactor, 1.1)):

        output = MeshOutput()

        output.write(simulator.simulation.world, file_name=str(testfile))


def test_mesh_output():
    output = MeshOutput()

    with pytest.raises(RuntimeError):
        output.display(None)


def test_plotrenderer_quit(simulator, monkeypatch, nop):
    monkeypatch.setattr(matplotlib.pyplot, 'ion', nop)
    monkeypatch.setattr(matplotlib.pyplot, 'show', nop)

    output = PlotRenderer()

    output.display(simulator.simulation.world)

    matplotlib.pyplot.close(output.fig.number)

    with pytest.raises(KeyboardInterrupt):
        output.display(simulator.simulation.world)


def test_mesh_cell_zoo(reset_state, simulator, tmpdir, add_cell_zoo):
    testfile = tmpdir.join('testfile.stl')

    add_cell_zoo(simulator)

    output = MeshOutput()

    output.write(simulator.simulation.world, file_name=str(testfile))


def test_render_debug(reset_state, simulator, tmpdir, add_cell_zoo, chdir):
    new_pwd = tmpdir.mkdir('debugout')
    testfile = tmpdir.join('testfile.png')

    add_cell_zoo(simulator)

    output = NoisyUnevenIlluminationPhaseContrast()
    output.write_debug_output = True

    with chdir(str(new_pwd)):
        output.write(simulator.simulation.world, file_name=str(testfile))

    assert len(new_pwd.listdir()) > 0


def test_render_bytescale_nochange():
    input = np.zeros((256, 256), dtype=np.uint8)

    assert id(bytescale(input)) == id(input)


def test_render_add_if_uneven():
    assert add_if_uneven(1) == 2
    assert add_if_uneven(2) == 2


def test_fluorescence_not_the_right_channel(
    reset_state, simulator, tmpdir, add_cell_zoo
):
    testfile = tmpdir.join('testfile.png')

    add_cell_zoo(simulator)

    output = FluorescenceRenderer()
    output.channel = 1

    output.write(simulator.simulation.world, testfile)


def test_render_multichannel_tif(
    reset_state, simulator, tmpdir, add_cell_zoo, tunables
):
    testfile = tmpdir.join('testfile.tif')

    add_cell_zoo(simulator)

    with tunables(
        (RenderChannels, 'NoisyUnevenIlluminationPhaseContrast, FluorescenceRenderer')
    ):
        output = TiffOutput()

        output.write(simulator.simulation.world, file_name=str(testfile))


def test_render_renderchannels_nonsense(tunables):
    assert not RenderChannels.test('foo')


def test_render_mock_failcv2(monkeypatch):
    def raise_cv2_error(*args, **kwargs):
        raise cv2.error()

    monkeypatch.setattr(cv2, 'haveImageWriter', raise_cv2_error)

    assert not cv2_has_write_support('.foo')


def test_render_scale_points_relative():
    points = np.linspace(0, 1)
    points = np.c_[points, points]
    scale_factor = 1.1
    scaled_points = scale_points_relative(points, scale_factor)

    assert_almost_equal(scaled_points.min(), -0.05)
    assert_almost_equal(scaled_points.max(), 1.05)


def test_render_scale_points_absolute_nop():
    points = np.linspace(0, 1)
    points = np.c_[points, points]

    scaled_points = scale_points_absolute(points)

    assert id(scaled_points) == id(points)


def test_render_get_canvas_points_for_cell(simulator, tunables):
    cell = simulator.simulation.world.cells[0]

    with tunables((RoiOutputScaleFactor, 1.0)):
        get_canvas_points_for_cell(cell)

    with tunables((RoiOutputScaleFactor, 1.1)):
        get_canvas_points_for_cell(cell)

    with tunables((RoiOutputScaleDelta, 0.0)):
        get_canvas_points_for_cell(cell)

    with tunables((RoiOutputScaleDelta, 0.1)):
        get_canvas_points_for_cell(cell)


def test_render_plainoutput_display_cv2(simulator, tunables, monkeypatch, nop):

    output = PlainRenderer()

    with tunables((OpenCVimshow, True)):
        monkeypatch.setattr(cv2, 'imshow', nop)
        monkeypatch.setattr(cv2, 'waitKey', nop)

        output.display(simulator.simulation.world)


def test_render_plainoutput_display_matplotlib(simulator, tunables, monkeypatch, nop):

    output = PlainRenderer()

    with tunables((OpenCVimshow, False)):
        monkeypatch.setattr(matplotlib.pyplot, 'ion', nop)
        monkeypatch.setattr(matplotlib.pyplot, 'show', nop)

        output.display(simulator.simulation.world)

        # the second call will be handled differently, hence we try it as well

        output.display(simulator.simulation.world)


def test_render_on_canvas_matplotlib_obscure_options(simulator, monkeypatch, nop):
    canvas = new_canvas()
    array_of_points = [
        get_canvas_points_raw(cell, canvas.shape[0])
        for cell in simulator.simulation.world.cells
    ]

    monkeypatch.setattr(matplotlib.pyplot, 'ion', nop)
    monkeypatch.setattr(matplotlib.pyplot, 'ioff', nop)

    monkeypatch.setattr(matplotlib.pyplot, 'isinteractive', lambda: True)

    render_on_canvas_matplotlib(canvas, array_of_points, over_sample=2)


def test_rle():
    mask = np.zeros((128, 128), dtype=bool)
    mask[32 : 32 + 64, 32 : 32 + 64] = 1

    result = binary_to_rle(mask)

    assert result.ravel().tolist() == ([4128] + ([64] * 127) + [4128])


def test_output_dummy():
    output = object.__new__(Output)
    output.output(None)
    output.write(None, None)

    with pytest.raises(RuntimeError):
        output.display(None)


def test_overwrite(tmpdir):
    testfile = tmpdir.join('testfile')
    testfile.write("Test")

    with pytest.raises(RuntimeError):
        check_overwrite(str(testfile), overwrite=False)


def test_ensure_extension():
    assert ensure_extension('Hello{}.txt', '.txt') == 'Hello.txt'


def test_mkdir(tmpdir):
    p = Path(str(tmpdir)) / "some" / "directories"

    some_file = p / "some_file"

    assert not p.exists()

    ensure_path(str(some_file))

    assert p.exists()
