import jsonpickle
import jsonpickle.ext.numpy
import jsonpickle.util
import numpy as np

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
if isinstance(jsonpickle.util.PRIMITIVES, tuple):
    jsonpickle.util.PRIMITIVES += additional_primitives
elif isinstance(jsonpickle.util.PRIMITIVES, set):
    for additional_primitive in additional_primitives:
        jsonpickle.util.PRIMITIVES.add(additional_primitive)
else:
    pass  # unexpected. maybe emit a warning


class JsonPickleSerializer(Output):
    def output(self, world, **kwargs):
        return jsonpickle.dumps(world)

    def write(self, world, file_name, overwrite=False, output_count=0, **kwargs):
        with open(
            check_overwrite(
                ensure_path_and_extension_and_number(file_name, '.json', output_count),
                overwrite=overwrite,
            ),
            'w+',
        ) as fp:
            fp.write(self.output(world))

    def display(self, world, **kwargs):
        print(self.output(world))


def type2numpy(value, max_len=None):
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


def prepare_numpy_dtype(inner, list_max_lens=None):
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
    def output(self, world, **kwargs):
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
        self, world, file_name, time=None, overwrite=False, output_count=0, **kwargs
    ):
        np.savez(
            check_overwrite(
                ensure_path_and_extension_and_number(file_name, '.npz', output_count),
                overwrite=overwrite,
            ),
            time=time,
            cells=self.output(world),
        )


__all__ = [
    'JsonPickleSerializer',
    'QuickAndDirtyTableDumper',
]
