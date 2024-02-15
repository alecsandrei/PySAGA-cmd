from src.saga import SAGA
import matplotlib.pyplot as plt


def main():
    saga = SAGA(saga_cmd='/usr/bin/saga_cmd')

    # Defining objects
    dem = './data/example_input/DEM_30m.tif'
    output = './data/example_output/flow_accumulation'

    # Defining libraries
    preprocessor = saga / 'ta_preprocessor'
    hydrology = saga / 'ta_hydrology'

    # Defining tools
    route_detection = preprocessor / 'Sink Drainage Route Detection'
    sink_removal = preprocessor / 'Sink Removal'
    flow_accumulation = hydrology / 'Flow Accumulation (Parallelizable)'

    # Piping
    pipe = (
        route_detection(elevation=dem, sinkroute='temp') |
        sink_removal(dem=route_detection.elevation,
                     sinkroute=route_detection.sinkroute,
                     dem_preproc='temp') |
        flow_accumulation(dem=sink_removal.dem_preproc, flow=output)
    )
    outputs = pipe.execute(verbose=True)

    # If you also install the extra dependencies, the following lines
    # of code are available and you can plot your output rasters.
    rasters = outputs[-1].get_raster('flow')
    raster = rasters[0].plot(cmap='Blues', norm='log',
                             cbar_kwargs=dict(label='log of accumulated flow'))
    raster.set_title('Flow accumulation map')
    plt.show()


if __name__ == '__main__':
    main()
