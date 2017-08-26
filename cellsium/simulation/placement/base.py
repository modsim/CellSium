from .. import BaseSimulator

from tunable import Tunable, Selectable

class PlacementSimulationSimplification(Tunable):
    """ How much the placement should be simplified, 0: use the normal shapes, 1: use simplified shapes, 2: use many-circle approximations """
    default = 0


class PlacementSimulation(BaseSimulator, Selectable):
    pass
