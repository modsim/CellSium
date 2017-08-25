from .. import Width, Height
from . import Output
from tunable import Tunable
from matplotlib import pyplot


class MicrometerPerCm(Tunable):
    default = 2.5


class PlotRenderer(Output, Output.Default):
    def __init__(self):
        super(PlotRenderer, self).__init__()

        self.fig = self.ax = None

    def output(self, world):
        if self.fig is None:
            self.fig = pyplot.figure(
                figsize=(Width.value / MicrometerPerCm.value / 2.51, Height.value / MicrometerPerCm.value / 2.51)
            )

        fig = self.fig

        if self.ax is None:
            self.ax = fig.add_subplot(111)

        ax = self.ax

        ax.clear()

        for cell in world.cells:
            points = cell.points_on_canvas()
            ax.plot(points[:, 0], points[:, 1])

        for boundary in world.boundaries:
            for start, stop in zip(boundary, boundary[1:]):
                ax.plot([start[0], stop[0]], [start[1], stop[1]])

        ax.set_xlim(0, Width.value)
        ax.set_ylim(0, Height.value)

        return fig, ax

    def write(self, world, file_name):
        fig, ax = self.output(world)
        fig.savefig(file_name)

    def display(self, world):
        pyplot.ion()
        self.output(world)
        pyplot.show()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
