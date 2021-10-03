from cellsium.model import assemble_cell, SimulatedCell, h_to_s, Square


class SquareCellModel(SimulatedCell):
    @staticmethod
    def random_sequences(sequence):
        return dict(elongation_rate=sequence.normal(1.5, 0.25))  # µm·h⁻¹

    def birth(self, parent=None, ts=None) -> None:
        self.elongation_rate = next(self.random.elongation_rate)
        self.division_time = h_to_s(1.0)

    def grow(self, ts) -> None:
        self.length += self.elongation_rate * ts.hours

        if ts.time > (self.birth_time + self.division_time):
            offspring_a, offspring_b = self.divide(ts)
            offspring_a.length = offspring_b.length = self.length / 2


Cell = assemble_cell(SquareCellModel, Square)
