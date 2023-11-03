import subprocess
from typing import Union
from attrs import define, field

import numpy as np
import rasterio as rio
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import matplotlib.pyplot as plt


@define
class Output:
    """This class represents the output of the 'run_command' method from the SAGA class of this module.

    Parameters
    ----------
    completed_process : subprocess.CompletedProcess
        The returned object from the 'subprocess.run' method.
    parameters : dict
        The kwargs used when executing the 'run_command' method from the SAGA class.
    
    Attributes
    ----------
    completed_process : subprocess.CompletedProcess
        The returned object from the 'subprocess.run' method.
    parameters : dict
        The kwargs used when executing the 'run_command' method from the SAGA class.
    text : str
        The captured stdout from the child process.
    """
    completed_process: subprocess.CompletedProcess
    parameters: dict
    text: str = field(init=False)

    def __attrs_post_init__(self):
        self.text = self.completed_process.stdout
    
    def _read_raster(self,
                     parameter: str,
                     nodata: Union[float, list] = -32768.0) -> tuple[rio.DatasetReader, np.array]:
        """This method will be used to read raster objects using rasterio.
        Args:
            parameter: The 'key' to access the parameter inside the 'parameters' attribute.
            nodata: A float or a list of floating points that will be used to set nodata values
                to the raster map. Defaults to -32768.0.

        Returns:
            tuple: A tuple containing a rasterio.DatasetReader and a numpy.array.
        """
        filepath = self.parameters[parameter]
        with rio.open(filepath) as src:
            array = src.read(1).astype("float")
            if isinstance(nodata, float):
                nodata = [nodata]
            for value in nodata:
                array[array == value] = np.nan
        return src, array

    def plot_raster(self,
                    parameter: str,
                    cmap='Greys_r',
                    nodata: Union[float, list[float]] = -32768.0,
                    ax: plt.Axes = None,
                    cbar=True,
                    **kwargs) -> GeoAxes:
        """This method can be used to plot rasters.
        Args:
            parameter: The 'key' to access the parameter inside the 'parameters' attribute.
            cmap: A matplotlib colormap. Defaults to 'Greys_r'. For more details run the following lines
                of code:
                >>> from matplotlib import colormaps
                >>> list(colormaps)
            nodata: A float or a list of floating points that will be used to set nodata values
                to the raster map. Defaults to -32768.0.
            ax: A matplotlib axes object. Defaults to None.
            cbar: Whether to add a colorbar or not. Defaults to True.
            **kwargs: Options to pass to the 'imshow' method of matplotlib.

        Returns:
            GeoAxes: A cartopy GeoAxes object.
        """
        src, array = self._read_raster(parameter, nodata=nodata)
        crs = str(src.crs).split(':')[-1]
        left, bottom, right, top = src.bounds
        proj = ccrs.epsg(crs)
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(projection=proj)
        im = ax.imshow(
                array,
                cmap=cmap,
                extent=(left, right, bottom, top),
                **kwargs)
        if cbar:
            cax = fig.add_axes([ax.get_position().x1+0.01,
                                ax.get_position().y0,
                                0.02,
                                ax.get_position().height])
            plt.colorbar(im, cax=cax)
        plt.show()
        return ax

    def plot_histogram(self,
                       parameter: str,
                       nodata: Union[float, list] = -32768.0,
                       ax=None,
                       **kwargs) -> plt.Axes:
        """This method can be used to plot a histogram of raster.
        Args:
            parameter: The 'key' to access the parameter inside the 'parameters' attribute.
            cmap: A matplotlib colormap. Defaults to 'Greys_r'. For more details run the following lines
                of code:
                >>> from matplotlib import colormaps
                >>> list(colormaps)
            nodata: A float or a list of floating points that will be used to set nodata values
                to the raster map. Defaults to -32768.0.
            ax: A matplotlib axes object. Defaults to None.
            **kwargs: Options to pass to the 'hist' method of matplotlib.

        Returns:
            plt.Axes: A matplotlib axes object.
        """
        _, array = self._read_raster(parameter, nodata=nodata)
        array = array.flatten()
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot()
        ax.hist(
            array,
            **kwargs
        )
        plt.show()
        return ax
