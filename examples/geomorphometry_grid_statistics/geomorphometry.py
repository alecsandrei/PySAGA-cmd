# This script is only an example on how to integrate PySAGA-cmd in your workflow.

import os
import glob
import tempfile

# Geopandas will be used to add a binary label to the watershed segments,
# more precisely the segments overlapping a landslided area will receive
# a '1' label, and those who do not overlap a landslided area will receive
# a '0' label. Landslided areas are not provided in the github repo and
# they have been manually digitized from a LiDAR DEM.
import geopandas as gpd
gpd.options.io_engine = 'pyogrio'

from PySAGA_cmd import SAGA, Output


class Geomorphometry:
    """
    This class will be used to generate first and second derivatives of elevation,
    as well as descriptive statistics of those derivatives. After generating the
    derivatives, watershed segments of vector ruggedness measure will be generated,
    converted to shapes and enriched with descriptives statistics of the derivatives
    of elevation.
    """

    def __init__(self, saga_cmd_dir: str, dem_dir: str, output_dir: str):
        self.saga_env = SAGA(sagacmd = saga_cmd_dir)
        self.dem_dir = dem_dir
        self.output_dir = output_dir
        self.temp_dir = tempfile.mkdtemp()
        self._hydro_dem_preprocessed = None
        self._vrm_watershed_segments = None
        self.tools = {
            'index_of_convergence': self.index_of_convergence,
            'terrain_surface_convexity': self.terrain_surface_convexity,
            'topographic_openness': self.topographic_openness,
            'slope_aspect_curvature': self.slope_aspect_curvature,
            'real_surface_area': self.real_surface_area,
            'wind_exposition_index': self.wind_exposition_index,
            'topographic_position_index': self.topographic_position_index,
            'valley_depth': self.valley_depth,
            'morphometric_protection_index': self.morphometric_protection_index,
            'terrain_ruggedness_index': self.terrain_ruggedness_index,
            'vector_ruggedness_measure': self.vector_ruggedness_measure,
            'terrain_surface_texture': self.terrain_surface_texture,
            'upslope_downslope_curvature': self.upslope_downslope_curvature,
            'flow_accumulation_parallelizable': self.flow_accumulation_parallelizable,
            'flow_path_length': self.flow_path_length,
            'slope_length': self.slope_length,
            'cell_balance': self.cell_balance,
            'saga_wetness_index': self.saga_wetness_index
        }

    @property
    def hydro_dem_preprocessed(self):
        """Get the temporary location of a hydrologically preprocessed dem."""
        if self._hydro_dem_preprocessed is None:
            sink_route_dir = self.temp_dir + '/sinkroute.tif'
            dem_preproc_dir = self.temp_dir + '/dem_preproc.tif'
            # Creating the sink route
            (self
            .saga_env
            .get_tool('ta_preprocessor', '1')
            .run_command(
                elevation=self.dem_dir,
                sinkroute=sink_route_dir,
                threshold='0',
                thrsheight='100.0')
            )
            # Removing sinks
            (self
            .saga_env
            .get_tool('ta_preprocessor', '2')
            .run_command(
                dem=self.dem_dir,
                sinkroute=sink_route_dir,
                dem_preproc=dem_preproc_dir,
                method='1',
                threshold='0',
                thrsheight='100.0')
            )
            self._hydro_dem_preprocessed = dem_preproc_dir
        return self._hydro_dem_preprocessed

    @property
    def vrm_watershed_segments(self):
        if self._vrm_watershed_segments is None:
            if 'vrm.tif' not in glob.glob(os.path.join(self.output_dir, '*.tif')):
                self.vector_ruggedness_measure()
            grid_input = self.output_dir + 'vrm.tif'
            grid_segments = self.temp_dir + '/vrm_watershed_segments.tif'
            shape_segments = self.output_dir + 'shapes/vrm_watershed_segments.shp'
            watershed_segmentation = self.saga_env.get_tool('imagery_segmentation', '0')
            watershed_segmentation.run_command(
                grid=grid_input,
                segments=grid_segments,
                seeds=self.temp_dir + '/seeds.shp',
                borders=self.temp_dir + '/borders.tif',
                output='1',
                down='0',
                join='0',
                threshold='0',
                edge='1',
                bborders='0'
            )
            watershed_segmentation_shapes = self.saga_env.get_tool('shapes_grid', '6')
            watershed_segmentation_shapes.run_command(
                grid=grid_segments,
                polygons=shape_segments,
                class_all='1',
                class_id='1',
                split='1',
                allvertices='0'
            )
            self._vrm_watershed_segments = shape_segments
        return self._vrm_watershed_segments

    @staticmethod
    def label_watershed_segments(segments: str) -> Output:
        """This method will label the segments. It will create
        a boolean 'landslide' field.  
        
        Args:
            segments (str): the folder location of the segments

        Returns:
            str: the folder location of the labeled segments
        """
        os.chdir('/media/alex/SSD_ALEX/scripts/geomorphology/test_areas/jijioara')
        labeled_segments_output = 'grids/output/shapes/vrm_watershed_segments_labeled.shp'
        training = gpd.read_file(r'alunecari_training.shp')
        testing = gpd.read_file(r'alunecari_testing.shp')
        segments = gpd.read_file(segments).drop(columns=['VALUE', 'NAME'])
        training_mask = segments.intersects(training.dissolve().geometry[0])
        testing_mask = segments.intersects(testing.dissolve().geometry[0])
        segments_landslide = ((training_mask + testing_mask) >= 1).astype(int)
        segments['landslide'] = segments_landslide
        segments.to_file(labeled_segments_output)
        print('Segments have been labeled.')
        return labeled_segments_output

    # First and second derivatives of elevation
    def index_of_convergence(self) -> Output:
        ioc = self.saga_env.get_tool('ta_morphometry', '1')
        output = ioc.run_command(
            elevation=self.dem_dir,
            result=self.output_dir + 'ioc.tif',
            method='0',
            neighbours='0',
        )
        return output
    
    def terrain_surface_convexity(self) -> Output:
        conv = self.saga_env.get_tool('ta_morphometry', '21')
        output = conv.run_command(
            dem=self.dem_dir,
            convexity=self.output_dir + 'conv.tif',
            kernel='0',
            type='0',
            epsilon='0',
            scale='10',
            method='1',
            dw_weighting='0',
            dw_idw_power='2.0',
            dw_bandwidth='1.0'
        )
        return output
    
    def topographic_openness(self) -> Output:
        to = self.saga_env.get_tool('ta_lighting', '5')
        output = to.run_command(
            dem=self.dem_dir,
            pos=self.output_dir + 'poso.tif',
            neg=self.output_dir + 'nego.tif',
            radius='10000',
            method='1',
            dlevel='3.0',
            ndirs='8'
        )
        return output
    
    def slope_aspect_curvature(self) -> Output:
        slope = self.saga_env.get_tool('ta_morphometry', '0')
        output = slope.run_command(
            elevation=self.dem_dir,
            slope=self.output_dir + 'slope.tif',
            # aspect=self.output_dir + 'aspect.tif',
            c_gene=self.output_dir + 'cgene.tif',
            c_prof=self.output_dir + 'cprof.tif',
            c_plan=self.output_dir + 'cplan.tif',
            c_tang=self.output_dir + 'ctang.tif',
            c_long=self.output_dir + 'clong.tif',
            c_cros=self.output_dir + 'ccros.tif',
            c_mini=self.output_dir + 'cmini.tif',
            c_maxi=self.output_dir + 'cmaxi.tif',
            c_tota=self.output_dir + 'ctota.tif',
            c_roto=self.output_dir + 'croto.tif',
            method='6',
            unit_slope='0',
            unit_aspect='0'
        )
        return output
    
    def real_surface_area(self) -> Output:
        area = self.saga_env.get_tool('ta_morphometry', '6')
        output = area.run_command(
            dem=self.dem_dir,
            area=self.output_dir + 'area.tif'
        )
        return output

    def wind_exposition_index(self) -> Output:
        exposition = self.saga_env.get_tool('ta_morphometry', '27')
        output = exposition.run_command(
            dem=self.dem_dir,
            exposition=self.output_dir + 'wind.tif',
            maxdist='300.0',
            step='15.0',
            oldver='0',
            accel='1.5',
            pyramids='0'
        )
        return output

    def topographic_position_index(self) -> Output:
        tpi = self.saga_env.get_tool('ta_morphometry', '18')
        output = tpi.run_command(
            dem=self.dem_dir,
            tpi=self.output_dir + 'tpi.tif',
            standard='0',
            radius_min='0',
            radius_max='100',
            dw_weighting='0',
            dw_idw_power='1.0',
            dw_idw_offset='1',
            dw_bandwidth='75.0'
        )
        return output
    
    def valley_depth(self) -> Output:
        valley_depth = self.saga_env.get_tool('ta_channels', '7')
        output = valley_depth.run_command(
            elevation=self.dem_dir,
            valley_depth=self.output_dir + 'vld.tif',
            # ridge_level=None
            threshold='1.0',
            nounderground='1',
            order='4'
        )
        return output

    def morphometric_protection_index(self) -> Output:
        mpi = self.saga_env.get_tool('ta_morphometry', '7')
        output = mpi.run_command(
            dem=self.dem_dir,
            protection=self.output_dir + 'mpi.tif',
            radius='2000'
        )
        return output
    
    def terrain_ruggedness_index(self) -> Output:
        tri = self.saga_env.get_tool('ta_morphometry', '16')
        output = tri.run_command(
            dem=self.dem_dir,
            tri=self.output_dir + 'tri.tif',
            distance_weighting_dw_weighting='0',
            distance_weighting_dw_idw_power='1.0',
            distance_weighting_dw_idw_offset='1',
            distance_weighting_dw_bandwidth='1.0'
        )
        return output
    
    def vector_ruggedness_measure(self) -> Output:
        vrm = self.saga_env.get_tool('ta_morphometry', '17')
        output = vrm.run_command(
            dem=self.dem_dir,
            vrm=self.output_dir + 'vrm.tif',
            mode='1',
            radius='1',
            dw_weighting='0',
            dw_idw_power='1.0',
            dw_idw_offset='1',
            dw_bandwidth='75.0'
        )
        return output

    def terrain_surface_texture(self) -> Output:
        texture = self.saga_env.get_tool('ta_morphometry', '20')
        output = texture.run_command(
            dem=self.dem_dir,
            texture=self.output_dir + 'txt.tif',
            epsilon='1',
            scale='10',
            method='1',
            dw_weighting='3',
            dw_idw_power='1',
            dw_idw_offset='1',
            dw_bandwidth='0.7'
        )
        return output
    
    def upslope_downslope_curvature(self) -> Output:
        upslope_downslope_curvature = self.saga_env.get_tool('ta_morphometry', '26')
        output = upslope_downslope_curvature.run_command(
            dem=self.dem_dir,
            c_local=self.output_dir + 'clo.tif',
            c_up=self.output_dir + 'cup.tif',
            c_up_local=self.output_dir + 'clu.tif',
            c_down=self.output_dir + 'cdo.tif',
            c_down_local=self.output_dir + 'cdl.tif',
            weighting='0.5'
        )
        return output
        
    def flow_accumulation_parallelizable(self) -> Output:
        flow_accumulation = self.saga_env.get_tool('ta_hydrology', '29')
        output = flow_accumulation.run_command(
            dem=self.hydro_dem_preprocessed,
            flow=self.output_dir + 'flo.tif',
            update='0',
            method='0',
            convergence='1.1'
        )
        return output

    def flow_path_length(self) -> Output:
        flow_path_length = self.saga_env.get_tool('ta_hydrology', '6')
        output = flow_path_length.run_command(
            elevation=self.hydro_dem_preprocessed,
            # seed=None,
            length=self.output_dir + 'fpl.tif',
            method='1',
            convergence='1.1'
        )
        return output

    def slope_length(self) -> Output:
        slope_length = self.saga_env.get_tool('ta_hydrology', '7')
        output = slope_length.run_command(
            dem=self.dem_dir,
            length=self.output_dir + 'spl.tif'
        )
        return output
    
    def cell_balance(self) -> Output:
        cell_balance = self.saga_env.get_tool('ta_hydrology', '10')
        output = cell_balance.run_command(
            dem=self.dem_dir,
            #weights=None,
            weights_default='1',
            balance=self.output_dir + 'cbl.tif',
            method='0'
        )
        return output
    
    def saga_wetness_index(self) -> Output:
        twi = self.saga_env.get_tool('ta_hydrology', '15')
        output = twi.run_command(
            dem=self.dem_dir,
            # weight=None,
            area=self.temp_dir + '/catchment_area.tif',
            slope=self.temp_dir + '/slope.tif',
            area_mod=self.temp_dir + '/catchment_area_mod.tif',
            twi=self.output_dir + 'twi.tif',
            suction='10.0',
            area_type='1',
            slope_type='1',
            slope_min='0.0',
            slope_off='0.1',
            slope_weight='1.0'
        )
        return output
    
    def execute_tools(self, tools: list[str] = None) -> None:
        if not tools:
            tools = list(self.tools.keys())
        for name in tools:
            self.tools[name]()
            print(f'{name} execution finished.')

    def grid_statistics_for_polygons(self) -> Output:
        # Use glob to find all files with a .tif extension
        grids = glob.glob(os.path.join(output_dir, '*.tif'))
        # Convert file names to full paths
        grids = [os.path.join(output_dir, grid) for grid in grids]
        # Add the DEM to the grids too
        grids.insert(0, self.dem_dir)
        grid_statistics_for_polygons = self.saga_env.get_tool('shapes_grid', '2')
        output = grid_statistics_for_polygons.run_command(
            grids=';'.join(grids),
            polygons=self.label_watershed_segments(self.vrm_watershed_segments),
            naming='1',
            method='0',
            parallelized='0',
            result=self.output_dir + 'shapes/watershed_segments_stats.shp',
            count='0',
            min='1',
            max='1',
            range='1',
            sum='1',
            mean='1',
            var='1',
            stddev='1',
            gini='0',
            quantiles='5; 25; 50; 75; 95'
        )
        return output


if __name__ == "__main__":
    dem_dir = r'/media/alex/SSD_ALEX/scripts/geomorphology/test_areas/jijioara/grids/DEM.tif' # here you input your dem location
    output_dir = r'/media/alex/SSD_ALEX/scripts/geomorphology/test_areas/jijioara/grids/output/' # here you put your output location, make sure to create a shapes subfolder inside it!
    geo = Geomorphometry('/usr/local/bin/saga_cmd', dem_dir, output_dir)
    geo.execute_tools()
    geo.grid_statistics_for_polygons()