import sys
from pathlib import Path

import pytest
import shutil

from src.utils import (
    check_is_executable,
    check_is_file,
    PathDoesNotExist,
    NotExecutableError
)


def test_check_is_file(tmp_path: Path):
    with pytest.raises(IsADirectoryError):
        check_is_file(path=tmp_path)
    text = test_check_is_file.__name__
    tmp_file = tmp_path / ''.join([text, '.txt'])
    tmp_file.write_text(text)
    assert check_is_file(tmp_file) is None
    with pytest.raises(PathDoesNotExist):
        shutil.rmtree(tmp_path)
        check_is_file(path=tmp_path)


def test_check_is_executable(tmp_path: Path):
    text = test_check_is_executable.__name__
    tmp_file = tmp_path / ''.join([text, '.txt'])
    tmp_file.write_text(data=text)
    with pytest.raises(NotExecutableError):
        check_is_executable(tmp_file)
    if sys.platform.startswith('win'):
        # TODO: do a similar test that runs on linux.
        tmp_file = tmp_path / ''.join([text, '.bat'])
        tmp_file.write_text(data='@echo off')
        assert check_is_executable(path=tmp_file) is None
    # elif sys.platform.startswith('linux'):
    #     text = test_check_is_executable.__name__
    #     tmp_file = tmp_path / ''.join([text, '.sh'])
    #     tmp_file.write_text(data='echo "Hello, World!"')
    #     tmp_file.chmod(0o755)
    #     assert check_is_executable(path=tmp_file) is None
