from tunable import Selectable

import numpy as np


class Output(Selectable):
    def output(self, world):
        pass

    def write(self, world, file_name):
        pass

    def display(self, world):
        raise RuntimeError('Not implemented')
