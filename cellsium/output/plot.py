from .. import Width, Height
from . import Output
from tunable import Tunable
from matplotlib import pyplot


class MicrometerPerCm(Tunable):
    default = 2.5


class PlotRenderer(Output):
    def __init__(self):
        super(PlotRenderer, self).__init__()

    def output(self):
        fig = pyplot.figure(
            figsize=(Width.value / MicrometerPerCm.value / 2.51, Height.value / MicrometerPerCm.value / 2.51)
        )
        ax = fig.add_subplot(111)

        for cell in self.cells:
            points = cell.points_on_canvas()
            ax.plot(points[:, 0], points[:, 1])

        for boundary in self.boundaries:
            for start, stop in zip(boundary, boundary[1:]):
                ax.plot([start[0], stop[0]], [start[1], stop[1]])

        ax.set_xlim(0, Width.value)
        ax.set_ylim(0, Height.value)

        return fig, ax

    def write(self, file_name):
        fig, ax = self.output()
        fig.savefig(file_name)

    def display(self):
        self.output()
        pyplot.show()
