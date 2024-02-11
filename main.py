from src.saga import SAGA
# import matplotlib.pyplot as plt

if __name__ == '__main__':
    dem = './data/example_input/DEM_30m.tif'
    shade = './data/example_output/shade.tif'
    saga_env = SAGA(saga_cmd='/usr/bin/saga_cmd')
    saga_lib = saga_env.get_library(library='ta_lighting')
    saga_tool = saga_lib.get_tool(tool='0')
    output = saga_tool.run_command(elevation=dem,
                                   shade=shade,
                                   method='2')
    rasters = output.get_raster(parameters=['shade', 'elevation'])

    # You can import matplotlib and run the methods below.
    # raster = rasters[0].plot()
    # plt.show()
