from tunable import Selectable

import numpy as np


class Output(Selectable, Selectable.Multiple):
    def output(self, world, **kwargs):
        pass

    def write(self, world, file_name, **kwargs):
        pass

    def display(self, world, **kwargs):
        raise RuntimeError('Not implemented')
