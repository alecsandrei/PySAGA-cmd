import sys
from pathlib import Path

import pytest

from PySAGA_cmd.saga import (
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
        command = ' '.join([f'"{self.dummy_executable}"', f'"{library}"'])
        assert str(lib.command) == command

    def test_get_library_div(self):
        lib_name = 'ta_morphometry'
        library_div = self.get_saga() / lib_name
        command = ' '.join(
            [f'"{self.dummy_executable}"',
             f'"{lib_name}"']
        )
        assert str(library_div.command) == command

    def test_get_tool(self):
        lib_name = 'ta_morphometry'
        tool_name = '0'
        tool = self.get_saga().get_tool(library=lib_name, tool=tool_name)
        command = ' '.join(
            [f'"{self.dummy_executable}"',
             f'"{lib_name}"',
             f'"{tool_name}"']
        )
        assert str(tool.command) == command

    def test_get_tool_div(self):
        lib_name = 'ta_morphometry'
        tool_name = '0'
        tool_div = self.get_saga() / lib_name / tool_name
        command = ' '.join(
            [f'"{self.dummy_executable}"',
             f'"{lib_name}"',
             f'"{tool_name}"']
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
        saga = SAGA(self.dummy_executable)
        saga.flag = '--help'
        lib = Library(
            saga=saga,
            library=name,
        )
        assert lib
        assert lib.flag == '--help'


class TestTool:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.dummy_executable = dummy_executable(tmp_path)

    def test_initialize(self):
        saga = SAGA(self.dummy_executable)
        lib_name = 'ta_morphometry'
        tool_name = '0'
        lib = Library(saga=saga, library=lib_name)
        lib.flag = '--help'
        tool = Tool(
            library=lib,
            tool=tool_name,
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
        assert params['elevation'] == str(elevation)
        assert params['slope'] == str(slope)

    def test_parameters_temp(self, tmp_path: Path):
        elevation = tmp_path / 'elevation.tif'
        slope = tmp_path / 'temp.tif'
        params = Parameters(
            elevation=elevation,
            slope=slope
        )
        assert params['slope'] != 'temp.tif'


class TestPipeline:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.dummy_executable = dummy_executable(tmp_path)

    def test_pipeline(self):
        saga = SAGA(saga_cmd=self.dummy_executable)
        preprocessor = saga / 'ta_preprocessor'
        sink_drainage_route_detection = preprocessor / '1'
        sink_removal = preprocessor / '2'
        flow_accumulation_parallelizable = saga / 'ta_hydrology' / '29'
        dem = 'temp'
        sinkroute = 'temp'
        dem_preproc = 'temp'
        flow_accumulation = 'temp'
        pipe = (
            sink_drainage_route_detection(elevation=dem, sinkroute=sinkroute) |
            (sink_removal(dem=sink_drainage_route_detection.elevation,
                          sinkroute=sink_drainage_route_detection.sinkroute,
                          dem_preproc=dem_preproc)) |
            (flow_accumulation_parallelizable(
                dem=sink_removal.dem_preproc,
                flow_accumulation=flow_accumulation))
        )
        assert pipe
