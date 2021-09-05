# noinspection PyPep8Naming
import xml.etree.ElementTree as ET

from tunable import Tunable

from ..parameters import Height, Width
from . import Output, check_overwrite, ensure_path_and_extension_and_number


class MicrometerPerCm(Tunable):
    """Calibration for outputs, micrometer per centimeter"""

    default = 2.5


class SvgRenderer(Output):
    @staticmethod
    def create_xml():
        root = ET.Element('svg')

        xml = ET.ElementTree(root)

        root.attrib['width'] = str(Width.value)
        root.attrib['height'] = str(Height.value)

        defs = ET.SubElement(root, 'defs')
        style = ET.SubElement(defs, 'style')

        style.attrib['type'] = 'text/css'
        style.text = """
        .cell {
            stroke: #005b82;
            stroke-width: 0.1px;
            fill: none;
        }
        .boundary {
            stroke: #005b82;
            stroke-width: 0.1px;
            fill: none;
        }
        """

        return xml

    def __init__(self):
        super().__init__()

        self.xml = self.create_xml()

        self.group_boundary = ET.SubElement(self.xml.getroot(), 'g')
        self.group_boundary.attrib['id'] = 'boundaries'
        self.group_cells_all = ET.SubElement(self.xml.getroot(), 'g')
        self.group_boundary.attrib['id'] = 'cells'

        self.boundaries_written = False

    @staticmethod
    def points_to_path(points):
        return 'M' + (''.join('L%f %f' % tuple(point) for point in points))[1:] + 'Z'

    def output(self, world, **kwargs):

        if not self.boundaries_written:

            for boundary in world.boundaries:
                boundary_element = ET.SubElement(self.group_boundary, 'path')
                boundary_element.attrib['class'] = 'boundary'
                boundary_element.attrib['d'] = self.points_to_path(boundary)

            self.boundaries_written = True

        # frame
        group = ET.SubElement(self.group_cells_all, 'g')
        group.attrib['id'] = 'frameXXX'

        for cell in world.cells:
            cell_path = ET.SubElement(group, 'path')
            cell_path.attrib['class'] = 'cell'
            cell_path.attrib['d'] = self.points_to_path(cell.points_on_canvas())

    def write(self, world, file_name, overwrite=False, output_count=0, **kwargs):
        self.output(world)
        self.xml.write(
            check_overwrite(
                ensure_path_and_extension_and_number(file_name, '.svg', output_count),
                overwrite=overwrite,
            ),
            encoding='utf-8',
        )

    def display(self, world, **kwargs):
        raise RuntimeError('Unsupported')


__all__ = ['SvgRenderer']
