from .. import Width, Height
from . import Output
from tunable import Tunable

import numpy as np

from stl import mesh


class MeshOutput(Output):
    def __init__(self):
        super(MeshOutput, self).__init__()

    def output(self):
        meshes = []

        for boundary in self.boundaries:
            pass

        for cell in self.cells:
            vertices, triangles = cell.points3d_on_canvas()

            meshes.append(dict(vertices=vertices, triangles=triangles))

        return meshes

    def write(self, file_name):
        meshes = self.output()

        stl_meshes = []

        for single_mesh in meshes:
            vertices, triangles = single_mesh['vertices'], single_mesh['triangles']
            data = mesh.Mesh(np.zeros(len(triangles), dtype=mesh.Mesh.dtype))
            for i, tri in enumerate(triangles):
                data.vectors[i, :] = vertices[tri, :]

            stl_meshes.append(data)

        result_mesh = mesh.Mesh(np.concatenate([single_mesh.data for single_mesh in stl_meshes]))
        result_mesh.save(file_name)

    def display(self):
        raise RuntimeError('Unsupported')

"""



        from matplotlib import pyplot
        from mpl_toolkits.mplot3d import Axes3D
        fig = pyplot.figure()
        ax = fig.add_subplot(111, projection='3d')


        ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2])

        ax.set_aspect('equal', 'datalim')
        pyplot.show()


"""