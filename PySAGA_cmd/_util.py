"""Module that contains useful utilities."""

from __future__ import annotations

import os
import sys
import subprocess


def check_is_file(path: str) -> None:
    """Checks if an input file is a file."""
    if os.path.isdir(path):
        raise IsADirectoryError(f'A directory instead of a file was provided.')
    elif not os.path.isfile(path):
        raise ValueError(f'The file at path "{path}" does not exist.')
    
def check_is_executable(path: str) -> None:
    """Checks if an input file is executable."""
    try:
        _ = subprocess.run(path, capture_output=True)
    except:
        raise

def get_sagacmd_default() -> str:
    """Returns the default path of the saga_cmd file."""
    if sys.platform.startswith('linux'):
        path = '/usr/local/bin/saga_cmd'
    elif sys.platform.startswith('win'):
        path = r'C:\Program Files\SAGA\saga_cmd.exe'
    else:
        raise ValueError('A "sagacmd" parameter was not provided.')
    return path

