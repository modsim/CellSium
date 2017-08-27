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
