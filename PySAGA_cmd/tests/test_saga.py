from pathlib import Path
from functools import cached_property

from PySAGA_cmd.saga import (
    SAGA,
    Library,
    Tool,
    Parameters
)
from PySAGA_cmd.utils import get_sample_dem


# In order to run the tests, saga_cmd needs to be found.
SAGA_ = SAGA()


class TestSaga:

    def test_get_library(self):
        library = 'ta_morphometry'
        lib = SAGA_.get_library(library=library)
        command = ' '.join([f'"{SAGA_.saga_cmd}"', f'"{library}"'])
        assert str(lib.command) == command

    def test_get_library_div(self):
        lib_name = 'ta_morphometry'
        library_div = SAGA_ / lib_name
        command = ' '.join(
            [f'"{SAGA_.saga_cmd}"',
             f'"{lib_name}"']
        )
        assert str(library_div.command) == command

    def test_get_tool(self):
        lib_name = 'ta_morphometry'
        tool_name = '0'
        tool = SAGA_.get_tool(library=lib_name, tool=tool_name)
        command = ' '.join(
            [f'"{SAGA_.saga_cmd}"',
             f'"{lib_name}"',
             f'"{tool_name}"']
        )
        assert str(tool.command) == command

    def test_get_tool_div(self):
        lib_name = 'ta_morphometry'
        tool_name = '0'
        tool_div = SAGA_ / lib_name / tool_name
        command = ' '.join(
            [f'"{SAGA_.saga_cmd}"',
             f'"{lib_name}"',
             f'"{tool_name}"']
        )
        assert str(tool_div.command) == command

    def test_flag(self):
        lib_name = 'ta_morphometry'
        tool_name = '0'
        tool = SAGA_.get_tool(library=lib_name, tool=tool_name)
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

    def test_initialize(self):
        name = 'ta_morphometry'
        SAGA_.flag = '--help'
        lib = Library(
            saga=SAGA_,
            library=name,
        )
        assert lib
        assert lib.flag == '--help'


class TestTool:

    def test_initalize(self):
        lib_name = 'ta_morphometry'
        tool_name = '0'
        lib = Library(saga=SAGA_, library=lib_name)
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

    def test_pipeline(self):
        preprocessor = SAGA_ / 'ta_preprocessor'
        sink_drainage_route_detection = preprocessor / '1'
        sink_removal = preprocessor / '2'
        flow_accumulation_parallelizable = SAGA_ / 'ta_hydrology' / '29'
        dem = 'temp'
        sinkroute = 'temp'
        dem_preproc = 'temp'
        flow_accumulation = 'temp'
        pipe = (
            sink_drainage_route_detection(elevation=dem, sinkroute=sinkroute) |
            sink_removal(dem=sink_drainage_route_detection.elevation,
                         sinkroute=sink_drainage_route_detection.sinkroute,
                         dem_preproc=dem_preproc) |
            flow_accumulation_parallelizable(
                dem=sink_removal.dem_preproc,
                flow_accumulation=flow_accumulation)
        )
        assert pipe


class TestExecution:

    def test_tool_execution(self, tmpdir: str):
        dem = get_sample_dem()
        hydro_preproc_dem = Path(tmpdir) / ''.join(['preproc_', dem.name])

        del SAGA_.flag
        # Defining libraries
        preprocessor = SAGA_ / 'ta_preprocessor'
        hydrology = SAGA_ / 'ta_hydrology'

        # Defining tools
        route_detection = preprocessor / 'Sink Drainage Route Detection'
        sink_removal = preprocessor / 'Sink Removal'
        flow_accumulation = hydrology / 'Flow Accumulation (Parallelizable)'

        # Piping
        pipe = (
            route_detection(elevation=dem, sinkroute='temp.sdat') |
            sink_removal(dem=route_detection.elevation,
                         sinkroute=route_detection.sinkroute,
                         dem_preproc='temp.sdat') |
            flow_accumulation(dem=sink_removal.dem_preproc,
                              flow=hydro_preproc_dem)
        )
        outputs = pipe.execute(verbose=False)
        assert len(outputs) == 3
        assert Path(route_detection.sinkroute).exists()
        assert Path(sink_removal.dem_preproc).exists()
        assert hydro_preproc_dem.exists()
