from tunable import Selectable

import numpy as np


class Output(Selectable):
    def __init__(self):
        self.cells = []
        self.boundaries = []

    def add(self, cell):
        self.cells.append(cell)

    def add_boundary(self, coordinates):
        self.boundaries.append(np.array(coordinates))

    def clear(self):
        self.cells.clear()
        self.boundaries.clear()

    def output(self):
        pass

    def write(self, file_name):
        pass

    def display(self):
        raise RuntimeError('Not implemented')
