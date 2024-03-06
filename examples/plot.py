import os
from pathlib import Path

from PySAGA_cmd import SAGA
import matplotlib.pyplot as plt
from matplotlib import gridspec


if __name__ == '__main__':

    here = Path(__file__)
    os.chdir(here.parent)

    dem = Path(__file__).parent / '../data/example_input/DEM_30m.tif'
    saga = SAGA('/usr/bin/saga_cmd')

    # Defining tools.
    slope_aspect_curvature = saga / 'ta_morphometry' / 0  # We can also use tool indices to access tools.
    shading = saga / 'ta_lighting' / 'Analytical Hillshading'

    # Executing tools.
    output1 = slope_aspect_curvature.execute(verbose=True, elevation=dem, slope='temp.sdat')
    elevation, slope = output1.get_raster(['elevation', 'slope'])

    output2 = shading.execute(verbose=True, elevation=dem, shade='temp.sdat', method='5')
    shading = output2.get_raster('shade')[0]

    fig = plt.figure(figsize=(15, 10))

    gs = gridspec.GridSpec(2, 2, height_ratios=[1.5, 1])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax3 = fig.add_subplot(gs[2])
    ax4 = fig.add_subplot(gs[3])

    # Maps
    elevation.plot(ax=ax1, cmap='terrain', cbar_kwargs=dict(label='Elevation (meters)'))
    slope.plot(ax=ax2, cmap='rainbow', cbar_kwargs=dict(label='Radians'))
    shading.plot(ax=ax1, cbar=False, alpha=0.45)
    ax1.set_title('Elevation map')
    ax2.set_title('Slope map')

    # Histograms
    hist_kwargs = {
        'bins': 15, 'alpha': 0.65,
        'facecolor': '#2ab0ff', 'edgecolor': '#169acf',
        'linewidth': 0.5
    }
    elevation.hist(ax=ax3, **hist_kwargs)
    slope.hist(ax=ax4, **hist_kwargs)

    plt.tight_layout()

    fig.savefig('../assets/plot1.png', dpi=300, bbox_inches='tight')

    saga.temp_dir_cleanup()
