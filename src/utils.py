"""Module that contains useful utilities."""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path


def check_is_file(path: Path) -> None:
    """Checks if an input file is a file.

    If path points to a file, returns None and does not raise any errors.
    """
    if not path.exists():
        raise PathDoesNotExist(
            f'The path {path} does not exist.'
        )
    if path.is_dir():
        raise IsADirectoryError(
            f'The path {path} points to a directory and not to a file.'
        )
    if not path.is_file():
        raise FileNotFoundError(
            f'The file at path "{path}" does not exist.'
        )


def check_is_executable(path: Path) -> None:
    """Checks if an input file is executable.

    If path points to an executable, returns None and does not raise any errors.
    """
    message = f'The file at path {path} is not an executable.'
    try:
        _ = subprocess.run(path, check=False, capture_output=True)
    except subprocess.SubprocessError as e:
        raise NotExecutableError(message) from e
    except OSError as e:
        raise NotExecutableError(message) from e


def get_sagacmd_default() -> Path:
    """Returns the default path of the saga_cmd file.

    A path is only returned if the operating system
    is either Linux or Windows. Otherwise, an error
    is raised.
    """
    if sys.platform.startswith('linux'):
        return Path('/usr/bin/saga_cmd')
    if sys.platform.startswith('win'):
        return Path(r'C:\Program Files\SAGA\saga_cmd.exe')
    raise OSError(
        'SAGA GIS is not available for your OS.'
    )


def infer_file_extension(path_to_file: Path) -> str:
    """Attemps to infer the SAGA GIS extension of a file.

    First it checks if there is a file with .shp extension
    that has the same name. It does the same for .sdat. If
    it doesn't find any file that meets this criteria, it
    chooses the file with the biggest size that has the same
    name.

    Args:
        path_to_file: Points to a file without a suffix.
    """
    files_in_dir = path_to_file.parent.iterdir()
    files_filtered = [file for file in files_in_dir
                      if file.stem == path_to_file.stem]
    has_shp = any(file.suffix == '.shp' for file in files_filtered)
    has_sdat = any(file.suffix == '.sdat' for file in files_filtered)
    if not files_filtered:
        return ''
    if has_shp and not has_sdat:
        return '.shp'
    elif not has_shp and has_sdat:
        return '.sdat'
    else:
        return (
            sorted(files_filtered, key=sys.getsizeof)[-1].suffix
        )


class NotExecutableError(Exception):
    """Raised when a system file can not be executed."""
    def __init__(self, message: str):
        self.message = message


class PathDoesNotExist(Exception):
    """Raised when a given path does not exist."""
    def __init__(self, message: str):
        self.message = message