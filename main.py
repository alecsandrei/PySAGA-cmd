from pathlib import Path

import matplotlib.pyplot as plt

from PySAGA_cmd import (
    SAGA,
    get_sample_dem
)


def main():
    saga = SAGA()

    # Defining objects.
    # In general, it's good behaviour to specify file extension.
    # So please, do specify them for output objects (you can even
    # do it for 'temp'!)

    dem = get_sample_dem()
    output = (
        Path(__file__).parent / 'data/example_output/flow_accumulation.sdat'
    )

    # Defining libraries
    preprocessor = saga / 'ta_preprocessor'
    hydrology = saga / 'ta_hydrology'

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
        flow_accumulation(dem=sink_removal.dem_preproc, flow=output)
    )
    outputs = pipe.execute(verbose=True)

    # If you also install the extra dependencies, the following lines
    # of code are available and you can plot your output rasters.
    raster = outputs[-1].rasters['flow']
    plot = raster.plot(cmap='Blues', norm='log',
                       cbar_kwargs=dict(label='log of accumulated flow'))
    plot.set_title('Flow accumulation map')
    plt.show()

    # Don't forget to clean up the temporary directory (if you used temp files).
    saga.temp_dir_cleanup()


if __name__ == '__main__':
    main()
