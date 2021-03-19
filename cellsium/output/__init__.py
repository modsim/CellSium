from pathlib import Path

from tunable import Selectable, Tunable


def ensure_path(path):

    path = Path(path)
    if not path.parent.is_dir():
        path.parent.mkdir(exist_ok=True)

    return str(path)


def ensure_extension(path, extension):
    path = Path(path)

    if not isinstance(extension, list):
        extension = [extension]

    if not path.suffix or path.suffix and path.suffix not in extension:
        path = path.parent / (path.name + extension[0])

    path = str(path)

    if OutputIndividualFilesWildcard.value in path:
        path = path.replace(OutputIndividualFilesWildcard.value, '')

    return path


def ensure_path_and_extension(path, extension):
    ensure_path(path)
    return ensure_extension(path, extension)


def ensure_number(path, number, disable_individual=False):
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
    path, extension, number, disable_individual=False
):
    path = ensure_number(path, number, disable_individual=disable_individual)
    return ensure_path_and_extension(path, extension)


def check_overwrite(path, overwrite=False):
    if Path(path).is_file() and not overwrite:
        raise RuntimeError(
            f"Requested existing {path!r} as output, but overwriting is disabled."
        )

    return path


class OutputIndividualFiles(Tunable):
    default = True


class OutputIndividualFilesZeros(Tunable):
    default = 3


class OutputIndividualFilesWildcard(Tunable):
    default = '{}'


class OutputReproducibleFiles(Tunable):
    default = True


class Output(Selectable, Selectable.Multiple):
    def output(self, world, **kwargs):
        pass

    def write(self, world, file_name, **kwargs):
        pass

    def display(self, world, **kwargs):
        raise RuntimeError('Not implemented')
