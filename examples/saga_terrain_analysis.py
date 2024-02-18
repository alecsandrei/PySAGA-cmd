from pathlib import Path
from typing import Callable
import concurrent.futures

from PySAGA_cmd.saga import (
    SAGA,
    Library,
    ToolOutput,
    Executable
)


class TerrainAnalysis(Executable):
    """This class can be used to calculate terrain analysis grids."""

    def execute(self, concurrency: bool = True):
        def _execute(tool: Callable):
            tool()
        if concurrency:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(_execute, self.tools)
        else:
            for tool in self.tools:
                tool()

    @property
    def morphometry(self) -> Library:
        return self.saga / 'ta_morphometry'

    @property
    def lighting(self) -> Library:
        return self.saga / 'ta_lighting'

    @property
    def channels(self) -> Library:
        return self.saga / 'ta_channels'

    @property
    def hydrology(self) -> Library:
        return self.saga / 'ta_hydrology'

    def index_of_convergence(self) -> ToolOutput:
        tool = self.morphometry / 'Convergence Index'
        out_path = self.out_dir / 'ioc.tif'
        return tool.execute(
            elevation=self.dem,
            result=out_path,
            method=0,
            neighbours=0,
            verbose=True,
        )

    def terrain_surface_convexity(self) -> ToolOutput:
        tool = self.morphometry / 'Terrain Surface Convexity'
        out_path = self.out_dir / 'conv.tif'
        return tool.execute(
            dem=self.dem,
            convexity=out_path,
            kernel=0,
            type=0,
            epsilon=0,
            scale=10,
            method=1,
            dw_weighting=3,
            dw_idw_power=2,
            dw_bandwidth=0.7,
            verbose=True
        )

    def topographic_openness(self) -> ToolOutput:
        tool = self.lighting / 'Topographic Openness'
        return tool.execute(
            dem=self.dem,
            pos=self.out_dir / 'poso.tif',
            neg=self.out_dir / 'nego.tif',
            radius=10000,
            directions=1,
            direction=315,
            ndirs=8,
            method=1,
            dlevel=3.0,
            unit=0,
            nadir=1,
            verbose=True
        )

    def slope_aspect_curvature(self) -> ToolOutput:
        tool = self.morphometry / 'Slope, Aspect, Curvature'
        return tool.execute(
            elevation=self.dem,
            slope=self.out_dir / 'slope.tif',
            c_gene=self.out_dir / 'cgene.tif',
            c_prof=self.out_dir / 'cprof.tif',
            c_plan=self.out_dir / 'cplan.tif',
            c_tang=self.out_dir / 'ctang.tif',
            c_long=self.out_dir / 'clong.tif',
            c_cros=self.out_dir / 'ccros.tif',
            c_mini=self.out_dir / 'cmini.tif',
            c_maxi=self.out_dir / 'cmaxi.tif',
            c_tota=self.out_dir / 'ctota.tif',
            c_roto=self.out_dir / 'croto.tif',
            method=6,
            unit_slope=0,
            unit_aspect=0,
            verbose=True
        )

    def real_surface_area(self) -> ToolOutput:
        tool = self.morphometry / 'Real Surface Area'
        return tool.execute(
            dem=self.dem,
            area=self.out_dir / 'area.tif',
            verbose=True
        )

    def wind_exposition_index(self) -> ToolOutput:
        tool = self.morphometry / 'Wind Exposition Index'
        return tool.execute(
            dem=self.dem,
            exposition=self.out_dir / 'wind.tif',
            maxdist=300,
            step=15,
            oldver=0,
            accel=1.5,
            pyramids=0,
            verbose=True
        )

    def topographic_position_index(self) -> ToolOutput:
        tool = self.morphometry / 'Topographic Position Index (TPI)'
        return tool.execute(
            dem=self.dem,
            tpi=self.out_dir / 'tpi.tif',
            standard=0,
            radius_min=0,
            radius_max=100,
            dw_weighting=0,
            dw_idw_power=2,
            dw_bandwidth=75,
            verbose=True
        )

    def valley_depth(self) -> ToolOutput:
        tool = self.channels / 'Valley Depth'
        return tool.execute(
            elevation=self.dem,
            valley_depth=self.out_dir / 'vld.tif',
            threshold=1,
            maxiter=0,
            nounderground=1,
            order=4,
            verbose=True
        )

    def morphometric_protection_index(self) -> ToolOutput:
        tool = self.morphometry / 'Morphometric Protection Index'
        return tool.execute(
            dem=self.dem,
            protection=self.out_dir / 'mpi.tif',
            radius=2000,
            verbose=True
        )

    def terrain_ruggedness_index(self) -> ToolOutput:
        tool = self.morphometry / 'Terrain Ruggedness Index (TRI)'
        return tool.execute(
            dem=self.dem,
            tri=self.out_dir / 'tri.tif',
            mode=1,
            radius=1,
            dw_weighting=0,
            dw_idw_power=2,
            dw_bandwidth=75,
            verbose=True
        )

    def vector_ruggedness_measure(self) -> ToolOutput:
        tool = self.morphometry / 'Vector Ruggedness Measure (VRM)'
        return tool.execute(
            dem=self.dem,
            vrm=self.out_dir / 'vrm.tif',
            mode=1,
            radius=1,
            dw_weighting=0,
            dw_idw_power=2,
            dw_bandwidth=75,
            verbose=True
        )

    def terrain_surface_texture(self) -> ToolOutput:
        tool = self.morphometry / 'Terrain Surface Texture'
        return tool.execute(
            dem=self.dem,
            texture=self.out_dir / 'txt.tif',
            epsilon=1,
            scale=10,
            method=1,
            dw_weighting=3,
            dw_idw_power=2,
            dw_bandwidth=0.7,
            verbose=True
        )

    def upslope_and_downslope_curvature(self) -> ToolOutput:
        tool = self.morphometry / 'Upslope and Downslope Curvature'
        return tool.execute(
            dem=self.dem,
            c_local=self.out_dir / 'clo.tif',
            c_up=self.out_dir / 'cup.tif',
            c_up_local=self.out_dir / 'clu.tif',
            c_down=self.out_dir / 'cdo.tif',
            c_down_local=self.out_dir / 'cdl.tif',
            weighting=0.5,
            verbose=True
        )

    def flow_accumulation_parallelizable(self) -> ToolOutput:
        tool = self.hydrology / 'Flow Accumulation (Parallelizable)'
        return tool.execute(
            dem=self.dem,
            flow=self.out_dir / 'flow.tif',
            update=0,
            method=2,
            convergence=1.1,
            verbose=True
        )

    def flow_path_length(self) -> ToolOutput:
        tool = self.hydrology / 'Flow Path Length'
        return tool.execute(
            elevation=self.dem,
            # seed=None,
            length=self.out_dir / 'fpl.tif',
            seeds_only=0,
            method=1,
            convergence=1.1
        )

    def slope_length(self) -> ToolOutput:
        tool = self.hydrology / 'Slope Length'
        return tool.execute(
            dem=self.dem,
            length=self.out_dir / 'spl.tif'
        )

    def cell_balance(self) -> ToolOutput:
        tool = self.hydrology / 'Cell Balance'
        return tool.execute(
            dem=self.dem,
            # weights=None,
            weights_default=1,
            balance=self.out_dir / 'cbl.tif',
            method=1
        )

    def saga_wetness_index(self) -> ToolOutput:
        tool = self.hydrology / 'SAGA Wetness Index'
        return tool.execute(
            dem=self.dem,
            # weight=None,
            # area=None,
            # slope=None,
            # area_mod=None,
            twi=self.out_dir / 'twi.tif',
            suction=10,
            area_type=2,
            slope_type=1,
            slope_min=0,
            slope_off=0.1,
            slope_weight=1
        )

    def __init__(self, saga_cmd_path: Path, dem: Path):
        self.saga = SAGA(saga_cmd_path)
        self.dem = dem
        self.out_dir = self.dem.parent

        self.tools: list[Callable[[], ToolOutput]] = [
            self.index_of_convergence,
            self.terrain_surface_convexity,
            self.topographic_openness,
            self.slope_aspect_curvature,
            self.real_surface_area,
            self.wind_exposition_index,
            self.topographic_position_index,
            self.valley_depth,
            self.morphometric_protection_index,
            self.terrain_ruggedness_index,
            self.vector_ruggedness_measure,
            self.terrain_surface_texture,
            self.upslope_and_downslope_curvature,
            self.flow_accumulation_parallelizable,
            self.flow_path_length,
            self.slope_length,
            self.cell_balance,
            self.saga_wetness_index
        ]


if __name__ == '__main__':
    saga_cmd = Path('/usr/local/bin/saga_cmd')
    sample_dem = Path('./example_data/DEM_30m.tif')
    analysis = TerrainAnalysis(saga_cmd, sample_dem)
    analysis.execute(concurrency=False)
