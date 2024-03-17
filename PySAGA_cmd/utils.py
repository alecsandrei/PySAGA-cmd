"""Module that contains useful utilities."""

from __future__ import annotations

import os
import sys
import subprocess
from typing import (
    Union,
    Iterable,
    Literal,
    Callable,
    Optional,
)
from pathlib import Path
from enum import (
    Enum,
    auto
)


HERE = Path(__file__).parent


class Platforms(Enum):
    WINDOWS = auto()
    LINUX = auto()
    MAC_OS = auto()


def get_user_platform() -> Optional[Platforms]:
    platform = sys.platform
    if platform == 'win32':
        return Platforms.WINDOWS
    elif platform.startswith('linux'):
        return Platforms.LINUX
    elif platform == 'darwin':
        return Platforms.MAC_OS
    return None


USER_PLATFORM = get_user_platform()


def check_is_file(path: Path) -> None:
    """Checks if an input file is a file.

    If path points to a file does not raise any errors.
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

    If path points to an executable no errors are raised.
    """
    message = f'The file at path {path} is not an executable.'
    try:
        _ = subprocess.run(path, check=False, capture_output=True)
    except subprocess.SubprocessError as e:
        raise NotExecutableError(message) from e
    except OSError as e:
        raise NotExecutableError(message) from e


def search_saga_cmd() -> Path:
    """Searches for the saga_cmd executable."""
    saga_cmd = SAGACMDSearcher().search_saga_cmd()
    if saga_cmd is None:
        raise FileNotFoundError('Could not find saga_cmd.')
    return saga_cmd


def infer_file_extension(path_to_file: Path) -> Path:
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
        suffix = ''
    elif has_shp and not has_sdat:
        suffix = '.shp'
    elif not has_shp and has_sdat:
        suffix = '.sdat'
    else:
        suffix = sorted(files_filtered, key=sys.getsizeof)[-1].suffix
    return path_to_file.with_suffix(suffix)


def dynamic_print(popen: subprocess.Popen[str]):
    while True:
        if popen.stdout is None:
            break
        output = popen.stdout.readline()
        if not output and popen.poll() is not None:
            break
        if output:
            output = output.strip()
            if '%' not in output:
                continue
            print(output.strip(), end=print_end(output), flush=True)
    return popen.poll()


def print_end(string: str) -> Literal['\n', '\r']:
    """The 'end' parameter is a newline or a carriage return character."""
    if '100' in string or any(char.isalpha() for char in string):
        return '\n'
    return '\r'


class NotExecutableError(Exception):
    """Raised when a system file can not be executed."""
    def __init__(self, message: str) -> None:
        self.message = message


class PathDoesNotExist(Exception):
    """Raised when a given path does not exist."""
    def __init__(self, message: str) -> None:
        self.message = message


PathLike = Union[str, os.PathLike]


class SAGACMDSearcher:
    """Implements the searching behaviour for saga_cmd.

    Inspired by the 'Rsagacmd' R package implementation.
    """

    def search_saga_cmd(self) -> Optional[Path]:
        if USER_PLATFORM == Platforms.LINUX:
            return self._search_linux()
        elif USER_PLATFORM == Platforms.WINDOWS:
            return self._search_windows()
        elif USER_PLATFORM == Platforms.MAC_OS:
            return self._search_mac_os()
        else:
            raise OSError('Can not search for saga_cmd on your OS.')

    def _search_mac_os(self) -> Optional[Path]:
        dirs = (
            '/Applications/SAGA.app/Contents/MacOS'
            '/usr/local/bin'
            '/Applications/QGIS.app/Contents/MacOS/bin'
        )
        file_name = 'saga_cmd'
        if (path := self._search_file(dirs, file_name)) is not None:
            try:
                check_is_executable(path)
            except NotExecutableError:
                return None
            else:
                return path
        return None

    def _search_windows(self) -> Optional[Path]:
        dirs = (
            'C:/Program Files/SAGA-GIS',
            'C:/Program Files (x86)/SAGA-GIS',
            'C:/SAGA-GIS',
            'C:/OSGeo4W',
            'C:/OSGeo4W64',
        )
        file_name = 'saga_cmd.exe'
        if (path := self._search_file(dirs, file_name)) is not None:
            try:
                check_is_executable(path)
            except NotExecutableError:
                return None
            else:
                return path
        return None

    def _search_linux(self) -> Optional[Path]:
        dirs = (
            '/usr',
        )
        file_name = 'saga_cmd'
        # Check if saga_cmd is in path.
        try:
            file_name_path = Path(file_name)
            check_is_executable(file_name_path)
            return file_name_path
        except NotExecutableError:
            if (path := self._search_file(dirs, file_name)) is not None:
                try:
                    check_is_executable(path)
                except NotExecutableError:
                    return None
                else:
                    return path
        return None

    @staticmethod
    def _search_file(
        dirs: Iterable[PathLike],
        file_name: str
    ) -> Optional[Path]:
        dirs_as_path = tuple(map(Path, dirs))
        for dir_ in dirs_as_path:
            if not dir_.is_dir():
                continue
            for cur_path, _, files in os.walk(dir_):
                if file_name in files:
                    path = dir_ / cur_path / file_name
                    try:
                        check_is_executable(path)
                        return path
                    except NotExecutableError:
                        continue
        return None


def depends(func: Callable):
    """A decorator to handle missing modules, providing a custom error."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ModuleNotFoundError as e:
            # Monkey patching the ModuleNotFoundError messsage.
            e.msg = (
                f'The PySAGA-cmd package depends on {e.name}. '
                'Make sure to pip install the package before calling '
                f'"{func.__name__}" again.'
            )
            raise e
    return wrapper
