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


def import_extras():  # noqa:F401
    try:
        import numpy as np  # noqa:F401
        import rasterio as rio  # noqa:F401
        import cartopy.crs as ccrs  # noqa:F401
        import matplotlib.axes as axes  # noqa:F401
        import matplotlib.pyplot as plt  # noqa:F401
        import geopandas as gpd

        gpd.options.io_engine = "pyogrio"
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            f'There was an error importing {e.name} as it is ' +
            'not installed. To install it, run ' +
            '"pip install PySAGA-cmd[extras]".'
        )


class NotExecutableError(Exception):
    """Raised when a system file can not be executed."""
    def __init__(self, message: str):
        self.message = message


class PathDoesNotExist(Exception):
    """Raised when a given path does not exist."""
    def __init__(self, message: str):
        self.message = message
