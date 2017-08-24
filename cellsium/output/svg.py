from .. import Width, Height
from . import Output
from tunable import Tunable


import xml.etree.ElementTree as ET


class MicrometerPerCm(Tunable):
    default = 2.5


class SvgRenderer(Output):
    def __init__(self):
        super(SvgRenderer, self).__init__()

        self.root = ET.Element('svg')

        self.xml = ET.ElementTree(self.root)

        self.root.attrib['width'] = str(Width.value)
        self.root.attrib['height'] = str(Height.value)

        defs = ET.SubElement(self.root, 'defs')
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

        self.group_boundary = ET.SubElement(self.root, 'g')
        self.group_cells_all = ET.SubElement(self.root, 'g')

    @staticmethod
    def points_to_path(points):
        return 'M' + (''.join('L%f %f' % tuple(point) for point in points))[1:] + 'Z'

    def output(self, world):
        for boundary in world.boundaries:
            boundary_element = ET.SubElement(self.group_boundary, 'path')
            boundary_element.attrib['class'] = 'boundary'
            boundary_element.attrib['d'] = self.points_to_path(boundary)

        # frame
        group = ET.SubElement(self.group_cells_all, 'g')

        for cell in world.cells:
            cell_path = ET.SubElement(group, 'path')
            cell_path.attrib['class'] = 'cell'
            cell_path.attrib['d'] = self.points_to_path(cell.points_on_canvas())

    def write(self, world, file_name):
        self.output(world)
        self.xml.write(file_name)

    def display(self, world):
        raise RuntimeError('Unsupported')

