"""Mesh output in the STL format."""
import numpy as np
from stl import Mesh, stl
from tunable import Tunable

from ..simulation.simulator import World
from . import (
    Output,
    OutputReproducibleFiles,
    check_overwrite,
    ensure_path_and_extension_and_number,
)


class MeshCellScaleFactor(Tunable):
    """Scale factor for mesh output"""

    default: float = 1.0


class MeshOutput(Output):
    """Mesh output in the STL format."""

    def __init__(self):
        super().__init__()

    def output(self, world: World, **kwargs) -> None:
        meshes = []

        # for boundary in world.boundaries:
        #     pass

        scale_props = ('width', 'length')

        for cell in world.cells:
            backup = {}

            if MeshCellScaleFactor.value != 1.0:
                for sp in scale_props:
                    if hasattr(cell, sp):
                        value = getattr(cell, sp)
                        backup[sp] = value
                        setattr(cell, sp, value * MeshCellScaleFactor.value)

            vertices, triangles = cell.points3d_on_canvas()

            for k, v in backup.items():
                setattr(cell, k, v)

            meshes.append(dict(vertices=vertices, triangles=triangles))

        return meshes

    def write(
        self,
        world: World,
        file_name: str,
        overwrite: bool = False,
        output_count: int = 0,
        **kwargs
    ) -> None:
        meshes = self.output(world)

        stl_meshes = []

        for single_mesh in meshes:
            vertices, triangles = single_mesh['vertices'], single_mesh['triangles']
            data = Mesh(np.zeros(len(triangles), dtype=Mesh.dtype))
            for i, tri in enumerate(triangles):
                data.vectors[i, :] = vertices[tri, :]

            stl_meshes.append(data)

        result_mesh = Mesh(
            np.concatenate([single_mesh.data for single_mesh in stl_meshes])
            if stl_meshes
            else np.zeros(0, dtype=Mesh.dtype)
        )

        if OutputReproducibleFiles.value:
            stl.HEADER_FORMAT = '{package_name} ({version})'

        result_mesh.save(
            check_overwrite(
                ensure_path_and_extension_and_number(file_name, '.stl', output_count),
                overwrite=overwrite,
            )
        )

    def display(self, world: World, **kwargs) -> None:
        # ax = fig.add_subplot(111, projection='3d')
        # ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2])
        # ax.set_aspect('equal', 'datalim')
        raise RuntimeError("Unsupported")


__all__ = ['MeshOutput']
