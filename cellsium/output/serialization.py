"""Serialization outputs."""
import csv
from typing import Any, Dict, Mapping, Optional

import jsonpickle
import jsonpickle.ext.numpy
import jsonpickle.util
import numpy as np

from ..simulation.simulator import World
from . import Output, check_overwrite, ensure_path_and_extension_and_number

jsonpickle.ext.numpy.register_handlers()
additional_primitives = (
    np.float32,
    np.float64,
    np.int8,
    np.int16,
    np.int32,
    np.int64,
    np.uint,
    np.uint8,
    np.uint16,
    np.uint32,
    np.uint64,
)

jsonpickle.util.PRIMITIVES = type(jsonpickle.util.PRIMITIVES)(
    list(jsonpickle.util.PRIMITIVES) + list(additional_primitives)
)


class JsonPickleSerializer(Output):
    """Output as jsonpickle serialized files."""

    def output(self, world: World, **kwargs) -> None:
        return jsonpickle.dumps(world)

    def write(
        self,
        world: World,
        file_name: str,
        overwrite: bool = False,
        output_count: int = 0,
        **kwargs
    ) -> None:
        with open(
            check_overwrite(
                ensure_path_and_extension_and_number(file_name, '.json', output_count),
                overwrite=overwrite,
            ),
            'w+',
        ) as fp:
            fp.write(self.output(world))

    def display(self, world: World, **kwargs) -> None:
        print(self.output(world))


def type2numpy(value: Any, max_len: int = None) -> str:
    if isinstance(value, int):
        return 'i8'
    elif isinstance(value, float):
        return 'f8'
    elif isinstance(value, list):
        if max_len is None:
            max_len = len(value)
        return '(' + str(max_len) + ',)' + type2numpy(value[0])
    else:
        raise RuntimeError('...')


def prepare_numpy_dtype(
    inner: Mapping[str, Any], list_max_lens: Optional[Mapping[str, int]] = None
) -> Dict[str, str]:
    return [
        (
            key,
            type2numpy(
                value,
                max_len=list_max_lens[key]
                if list_max_lens and key in list_max_lens
                else None,
            ),
        )
        for key, value in sorted(inner.items())
    ]


class QuickAndDirtyTableDumper(Output):
    """Simple tabular output."""

    def output(self, world: World, **kwargs) -> None:
        if not world.cells:
            return np.zeros(0)

        first_cell = world.cells[0]
        list_lens = [
            {
                key: len(value)
                for key, value in celldict.items()
                if isinstance(value, list)
            }
            for celldict in (cell.__dict__ for cell in world.cells)
        ]

        list_max_lens = {
            key: max([list_len[key] for list_len in list_lens])
            for key in list_lens[0].keys()
        }

        dtype = prepare_numpy_dtype(first_cell.__dict__, list_max_lens=list_max_lens)

        cell_count = len(world.cells)

        array = np.zeros((cell_count,), dtype=dtype).view(np.recarray)

        for n in range(cell_count):
            for k, _ in dtype:
                setattr(array[n], k, getattr(world.cells[n], k))

        return array

    def write(
        self,
        world: World,
        file_name: str,
        time: Optional[float] = None,
        overwrite: bool = False,
        output_count: int = 0,
        **kwargs
    ):
        np.savez(
            check_overwrite(
                ensure_path_and_extension_and_number(file_name, '.npz', output_count),
                overwrite=overwrite,
            ),
            time=time,
            cells=self.output(world),
        )


class CsvOutput(Output):
    """CSV Tabular Output."""

    def output(self, world: World, time: Optional[float] = None, **kwargs) -> None:
        return [{**cell.__dict__, 'time': time} for cell in world.cells]

    def write(
        self,
        world: World,
        file_name: str,
        time: Optional[float] = None,
        overwrite: bool = False,
        output_count: int = 0,
        **kwargs
    ):
        rows = self.output(world, time=time)
        header = list(sorted(rows[0].keys()))

        with open(
            check_overwrite(
                ensure_path_and_extension_and_number(file_name, '.csv', output_count),
                overwrite=overwrite,
            ),
            'w',
            newline='',
        ) as fp:
            writer = csv.writer(fp)

            writer.writerow(header)

            for row in rows:
                writer.writerow(
                    [row[column] if column in row else '' for column in header]
                )


__all__ = [
    'JsonPickleSerializer',
    'QuickAndDirtyTableDumper',
    'CsvOutput',
]
