"""Cell parameter random initializations."""
from typing import Any, Dict

import numpy as np

from ..parameters import (
    Height,
    NewCellBendLowerLower,
    NewCellBendLowerUpper,
    NewCellBendOverallLower,
    NewCellBendOverallUpper,
    NewCellBendUpperLower,
    NewCellBendUpperUpper,
    NewCellLength1Mean,
    NewCellLength1Std,
    NewCellLength2Mean,
    NewCellLength2Std,
    NewCellLengthAbsoluteMax,
    NewCellLengthAbsoluteMin,
    NewCellRadiusFromCenter,
    NewCellWidthAbsoluteMax,
    NewCellWidthAbsoluteMin,
    NewCellWidthMean,
    NewCellWidthStd,
    Width,
)
from ..random import RRF, enforce_bounds

RandomSequenceType = Dict[str, Any]


class RandomWidthLength:
    """Random initializations for cell width/lengths."""

    @staticmethod
    def random_sequences(sequence: RRF) -> RandomSequenceType:

        assert NewCellLength1Mean.value > NewCellWidthMean.value
        assert NewCellLength2Mean.value > NewCellWidthMean.value

        def ensure_length_greater_width(length, width):
            for inner_length, inner_width in zip(length, width):
                if inner_length > inner_width:
                    yield [inner_length, inner_width]

        return dict(
            length__width=RRF.chain(
                ensure_length_greater_width,
                length=RRF.compose(
                    lambda raw_lengths, choice: raw_lengths[choice],
                    raw_lengths=RRF.chain(
                        enforce_bounds,
                        iterator=sequence.multivariate_normal(
                            [NewCellLength1Mean.value, NewCellLength2Mean.value],
                            [
                                [NewCellLength1Std.value, 0.0],
                                [0.0, NewCellLength2Std.value],
                            ],
                        ),
                        minimum=NewCellLengthAbsoluteMin.value,
                        maximum=NewCellLengthAbsoluteMax.value,
                    ),
                    choice=sequence.integers(0, 1),
                ),
                width=RRF.chain(
                    enforce_bounds,
                    iterator=sequence.normal(
                        NewCellWidthMean.value, NewCellWidthStd.value
                    ),
                    minimum=NewCellWidthAbsoluteMin.value,
                    maximum=NewCellWidthAbsoluteMax.value,
                ),
            )
        )


class RandomBentRod:
    """Random initializations for cell bent radii."""

    @staticmethod
    def random_sequences(sequence: RRF) -> RandomSequenceType:
        return dict(
            bend_overall=sequence.uniform(
                NewCellBendOverallLower.value,
                NewCellBendOverallUpper.value,
            ),
            bend_upper=sequence.uniform(
                NewCellBendUpperLower.value, NewCellBendUpperUpper.value
            ),
            bend_lower=sequence.uniform(
                NewCellBendLowerLower.value, NewCellBendLowerUpper.value
            ),
        )


class RandomPosition:
    """Random initializations for cell positions."""

    @staticmethod
    def random_sequences(sequence: RRF) -> RandomSequenceType:
        return dict(
            position=RRF.compose(
                lambda radius, angle: [
                    float(radius * np.cos(angle) + Width.value / 2),
                    float(radius * np.sin(angle) + Height.value / 2),
                ],
                radius=sequence.uniform(0, NewCellRadiusFromCenter.value),
                angle=RRF.wrap(sequence.uniform(0, 360.0), np.radians),
            )
        )


class RandomAngle:
    """Random initializations for cell angles."""

    @staticmethod
    def random_sequences(sequence: RRF) -> RandomSequenceType:
        return dict(angle=RRF.wrap(sequence.uniform(0, 360.0), np.radians))


class RandomFluorescence:
    """Random initializations for fluorescences."""

    @staticmethod
    def random_sequences(sequence: RRF) -> RandomSequenceType:
        return dict(fluorescences=sequence.uniform(0, 360.0, (1,)))
