import sys
from pathlib import Path

import pytest

from src.saga import (
    SAGA,
    Library,
    Tool,
    Parameters
)


def dummy_executable(tmp_path: Path):
    text = dummy_executable.__name__
    if sys.platform.startswith('win'):
        tmp_file = tmp_path / ''.join([text, '.bat'])
        tmp_file.write_text(data='@echo off')
    elif sys.platform.startswith('linux'):
        text = dummy_executable.__name__
        tmp_file = tmp_path / ''.join([text, '.sh'])
        tmp_file.write_text(data='#!/bin/sh')
        tmp_file.chmod(tmp_file.stat().st_mode | 0o755)
    return tmp_file


class TestSaga:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.dummy_executable = dummy_executable(tmp_path)

    def get_saga(self):
        return SAGA(saga_cmd=self.dummy_executable)

    def test_get_library(self):
        library = 'ta_morphometry'
        lib = self.get_saga().get_library(library=library)
        command = ' '.join([self.dummy_executable.as_posix(), library])
        assert str(lib.command) == command

    def test_get_library_div(self):
        lib_name = 'ta_morphometry'
        library_div = self.get_saga() / lib_name
        command = ' '.join(
            [self.dummy_executable.as_posix(),
             lib_name]
        )
        assert str(library_div.command) == command

    def test_get_tool(self):
        lib_name = 'ta_morphometry'
        tool_name = '0'
        tool = self.get_saga().get_tool(library=lib_name, tool=tool_name)
        command = ' '.join(
            [self.dummy_executable.as_posix(),
             lib_name,
             tool_name]
        )
        assert str(tool.command) == command

    def test_get_tool_div(self):
        lib_name = 'ta_morphometry'
        tool_name = '0'
        tool_div = self.get_saga() / lib_name / tool_name
        command = ' '.join(
            [self.dummy_executable.as_posix(),
             lib_name,
             tool_name]
        )
        assert str(tool_div.command) == command

    def test_flag(self):
        lib_name = 'ta_morphometry'
        tool_name = '0'
        tool = self.get_saga().get_tool(library=lib_name, tool=tool_name)
        flag = '--cores=8'
        tool.flag = flag
        assert tool.flag == flag
        assert tool.command[1] == flag
        tool.flag = None
        assert not tool.flag
        tool.flag = flag
        del tool.flag
        assert not tool.flag


class TestLibrary:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.dummy_executable = dummy_executable(tmp_path)

    def test_initialize(self):
        name = 'ta_morphometry'
        lib = Library(
            saga_cmd=self.dummy_executable,
            library=name,
            flag='help'
        )
        assert lib
        assert lib.flag == '--help'


class TestTool:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.dummy_executable = dummy_executable(tmp_path)

    def test_initialize(self):
        lib_name = 'ta_morphometry'
        tool_name = '0'
        lib = Library(saga_cmd=self.dummy_executable, library=lib_name)
        tool = Tool(
            library=lib,
            tool=tool_name,
            saga_cmd=self.dummy_executable,
            flag='help'
        )
        assert tool
        assert tool.flag == '--help'


class TestParameters:

    def test_parameters(self, tmp_path: Path):
        elevation = tmp_path / 'elevation.tif'
        slope = tmp_path / 'slope.tif'
        params = Parameters(
            elevation=elevation,
            slope=slope
        )
        assert params[0] == ''.join(['-ELEVATION=', str(elevation)])
        assert params[1] == ''.join(['-SLOPE=', str(slope)])
