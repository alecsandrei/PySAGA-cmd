# PySAGA-cmd
PySAGA-cmd is a simple way of running SAGA GIS tools using Python.

## How to download

Binary installers for the latest released version are available at the [Python Package Index (PyPI)](https://pypi.org/project/PySAGA-cmd/). If you want to have access to extra features (like plotting) you can download the extras as shown in the second command.
```sh
pip install PySAGA-cmd
pip install PySAGA-cmd[extras]
```

## How to use the package

### Choosing tools

Before you can use this package, you need to locate the **saga_cmd** in your system. For linux, it can be found somewhere in the `/usr/bin/` structure. For Windows, it is usually located in `C:\Program Files\SAGA`.

```python
from PySAGA_cmd import SAGA


saga = SAGA('/usr/bin/saga_cmd')

# Choosing libraries.
preprocessor = saga / 'ta_preprocessor'

# Choosing tools.
route_detection = preprocessor / 'Sink Drainage Route Detection'
sink_removal = preprocessor / 'Sink Removal'
flow_accumulation = saga / 'ta_hydrology' / 'Flow Accumulation (Parallelizable)'
```

### Executing

Executing an executable object is straight forward. For tools, just provide the required keyword arguments to the *execute* method.

```python
# Executing the SAGA object. Useful when you want to see the available libraries.
saga_output = saga.execute()
print(saga_output.text)

# Executing the Library object. Useful when you want to see the available tools.
preprocessor_output = preprocessor.execute()
print(preprocessor_output.text)

# Executing a Tool object.
dem = './data/example_input/DEM_30m.tif'
output = 'path/to/output.sdat'
output = route_detection.execute(verbose=True, elevation=dem, sinkroute=output)
print(output.text)
```

### Using flags

You can provide flags for SAGA, Library and Tool objects. To see what kind of flags we can use, we can look at the output of the following.

```python
saga.flag = 'help'
print(saga.execute().text)
```

### Chaining commands

Chaining commands can be done with **PySAGA-cmd** with the truediv operator. Consider the following example where the goal is to get a hydrologically preprocessed DEM and use that as input for the *Flow Accumulation (Parallelizable)* tool.

```python
pipe = (
    route_detection(elevation=dem, sinkroute='temp.sdat') |
    sink_removal(dem=route_detection.elevation,
                 sinkroute=route_detection.sinkroute,
                 dem_preproc='temp.sdat') |
    flow_accumulation(dem=sink_removal.dem_preproc, flow=output)
)
outputs = pipe.execute(verbose=True)
```

Notice the use of the truediv operator. Also, notice how we can create temporary intermediate files by using **temp** as the path. This is useful because we didn't care about the sinkroute and dem_preproc grids and we didn't want to save them, we only wanted to use them as input for other tools.

To visualize the temporary files, access the **temp_files** attribute of SAGA.

```python
print(saga.temp_dir)
print(saga.temp_files)
```

After you are done, don't forget to clean up the temporary folder (if you used temporary files).

```python
saga.temp_dir_cleanup()
```

### Plotting

After the execution of a *Tool*, we can use the returned *Output* object to plot the results.

```python
# If you set a flag to the SAGA object that would stop the tool
# from working (like 'help'), make sure to remove it before accesing
# the tools, like so:
saga.flag = None

# Defining tools.
slope_aspect_curvature = saga / 'ta_morphometry' / 0  # We can also use tool indices to access.
shading = saga / 'ta_lighting' / 'Analytical Hillshading'

# Executing tools.
output1 = slope_aspect_curvature.execute(verbose=True, elevation=dem, slope='temp.sdat')
elevation, slope = output1.get_raster(['elevation', 'slope'])

output2 = shading.execute(verbose=True, elevation=dem, shade='temp.sdat', method='5')
shading = output2.get_raster('shade')[0]


import matplotlib.pyplot as plt
from matplotlib import gridspec


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
ax1.set_title('Elevation map (hydrologically preprocessed)')
ax2.set_title('Slope map')
 
# Histograms
hist_kwargs = {
    'bins': 15, 'alpha': 0.65,
    'facecolor': '#2ab0ff', 'edgecolor':'#169acf',
    'linewidth': 0.5
}
elevation.hist(ax=ax3, **hist_kwargs)
slope.hist(ax=ax4, **hist_kwargs)
 
plt.tight_layout()
```
<img src="./assets/plot1.png" />

For extra information on how to use the package, you can also look at the [notebooks](https://github.com/alecsandrei/PySAGA-cmd/tree/master/examples/notebooks) inside the examples folder on the Github page.


# TODO before the launch of v1.0.0.

- [x] Remove all dependencies. All the dependencies will be turned into extra dependencies. Switch from attrs to dataclasses.
- [x] Write simple tests.
- [x] Add a Pipeline object.
- [ ] Use a tool like zest.releaser to release v1.0.0.
- [x] Update notebook examples with new API and README.md.
- [x] Make objects more pythonic.