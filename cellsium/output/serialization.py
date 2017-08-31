from . import Output

import jsonpickle


class JsonPickleSerializer(Output):
    def output(self, world):
        return jsonpickle.dumps(world)

    def write(self, world, file_name):
        with open(file_name, 'w+') as fp:
            fp.write(self.output(world))

    def display(self, world):
        print(self.output(world))




import numpy as np

def type2numpy(value):
    if isinstance(value, int):
        return 'i8'
    elif isinstance(value, float):
        return 'f8'
    elif isinstance(value, list):
        return str(len(value)) + type2numpy(value[0])
    else:
        raise RuntimeError('...')


# dir(C);val = getattr(C, k);if k.startswith('__') or hasattr(val, '__call__') or hasattr(val, '__next__'):

def prepare_numpy_dtype(inner):
    return [(key, type2numpy(value)) for key, value in sorted(inner.items())]


class QuickAndDirtyTableDumper(Output):
    def output(self, world):
        first_cell = world.cells[0]
        cell_count = len(world.cells)

        dtype = prepare_numpy_dtype(first_cell.__dict__)
        array = np.zeros((cell_count,), dtype=dtype).view(np.recarray)

        for n in range(cell_count):
            for k, _ in dtype:
                setattr(array[n], k, getattr(world.cells[n], k))

        return array

    def write(self, world, file_name, time=None):
        np.savez(file_name, time=time, cells=self.output(world))

