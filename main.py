from src.saga import SAGA
import matplotlib.pyplot as plt

if __name__ == '__main__':
    saga = SAGA(saga_cmd='/usr/bin/saga_cmd')

    # Defining objects
    dem = './data/example_input/DEM_30m.tif'
    output = './data/example_output/flow_accumulation.sdat'

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
        sink_removal(dem='_elevation', sinkroute='_sinkroute',
                     dem_preproc='temp') |
        flow_accumulation(dem='_dem_preproc', flow=output)
    )
    outputs = pipe.execute(verbose=True)

    # You can import matplotlib and run the methods below.
    rasters = outputs[-1].get_raster('flow')
    raster = rasters[0].plot(cmap='hsv')
    plt.show()
