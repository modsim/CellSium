"""The output package contains the various output modules."""
from pathlib import Path
from typing import Any, Optional, Tuple

from tunable import Selectable, Tunable

from ..simulation.simulator import World

ShapeType = Tuple[int, int]


def ensure_path(path: str) -> str:
    """
    Ensures that the parent directory to the to path exists.

    :param path: Path
    :return: the path
    """

    path = Path(path)
    if not path.parent.is_dir():
        path.parent.mkdir(parents=True, exist_ok=True)

    return str(path)


def ensure_extension(path: str, extension: str) -> str:
    """
    Ensures that the path ends with extension, possibly adding it.

    :param path: Path
    :param extension: Extension
    :return: Final path
    """
    path = Path(path)

    if not isinstance(extension, list):
        extension = [extension]

    if not path.suffix or path.suffix and path.suffix not in extension:
        path = path.parent / (path.name + extension[0])

    path = str(path)

    if OutputIndividualFilesWildcard.value in path:
        path = path.replace(OutputIndividualFilesWildcard.value, "")

    return path


def ensure_path_and_extension(path: str, extension: str) -> str:
    """
    Ensures that the parent directory to path exists,
    and it has extension, possibly by adding it.

    :param path: Path
    :param extension: Extension
    :return: Final path
    """
    ensure_path(path)
    return ensure_extension(path, extension)


def ensure_number(path: str, number: int, disable_individual: bool = False) -> str:
    """
    Depending on configuration, add a number to the path for consecutive output files.

    :param path: Path
    :param number: Number
    :param disable_individual: Possibility to disable adding of a number
    :return: Path with number
    """
    if OutputIndividualFiles.value and not disable_individual and number != -1:
        path = Path(path)

        stem = path.stem
        if OutputIndividualFilesWildcard.value not in stem:
            stem += OutputIndividualFilesWildcard.value

        digits = OutputIndividualFilesZeros.value

        stem = stem.replace(OutputIndividualFilesWildcard.value, f"{number:0>{digits}}")

        path = path.parent / (stem + path.suffix)

        path = str(path)

    return path


def ensure_path_and_extension_and_number(
    path: str, extension: str, number: int, disable_individual: bool = False
) -> str:
    """
    Ensures that a path exists, has an extension and a number.

    :param path: Path
    :param extension: Extension
    :param number: Number
    :param disable_individual: Whether to disable adding of number
    :return: Final path
    """
    path = ensure_number(path, number, disable_individual=disable_individual)
    return ensure_path_and_extension(path, extension)


def check_overwrite(path: str, overwrite: bool = False) -> str:
    """
    Check if a path exists, if so raising a RuntimeError if overwriting is disabled.

    :param path: Path
    :param overwrite: Whether to overwrite
    :return: Path
    """
    if Path(path).is_file() and not overwrite:
        raise RuntimeError(
            f"Requested existing {path!r} as output, but overwriting is disabled."
        )

    return path


class OutputIndividualFiles(Tunable):
    """Output individual files"""

    default: bool = True


class OutputIndividualFilesZeros(Tunable):
    """Amount of digits used for outputting the frame number of individual file names"""

    default: int = 3


class OutputIndividualFilesWildcard(Tunable):
    """Pattern for individual file names"""

    default: str = '{}'


class OutputReproducibleFiles(Tunable):
    """Output files in a reproducible manner"""

    default: bool = True


class Output(Selectable, Selectable.Multiple):
    """
    Base class of the Output classes.
    """

    def output(self, world: World, **kwargs) -> Optional[Any]:
        """
        Outputs the World, this function is usually called by either write or display.

        :param world: World
        :param kwargs: Additional arguments
        :return:
        """
        pass

    def write(self, world: World, file_name: str, **kwargs) -> None:
        """
        Output and write the World to file_name.

        :param world: World
        :param file_name: Filename to write output to
        :param kwargs: Additional arguments
        :return:
        """
        pass

    def display(self, world: World, **kwargs) -> None:
        """
        Output and display the World, e.g. via a GUI window.

        :param world: World
        :param kwargs: Additional arguments
        :return:
        """
        raise RuntimeError("Not implemented")
