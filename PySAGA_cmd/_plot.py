"""Plotting and other utilities for raster and vector objects."""

from typing import Union

from attrs import define

import numpy as np
import rasterio as rio
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import matplotlib.pyplot as plt
import geopandas as gpd
gpd.options.io_engine = "pyogrio"

@define
class Raster:
    """A raster image object.
    
    Parameters
    ----------
    path: The file path of the raster image.

    Methods
    ----------
    plot: Plots the raster file. Returns a 'GeoAxes' object.
    histogram: Plots a histogram of the raster file. Returns an 'Axes' object.
    to_numpy: Returns the Raster object as a 'np.array' object.
    """

    path: str

    def _read_raster(self,
                     nodata: Union[float, list] = -32768.0) -> tuple[rio.DatasetReader, np.array]:
        """This method will be used to read raster objects using rasterio.
        
        Args:
            parameter: The 'key' to access the parameter inside the 'parameters' attribute.
            nodata: A float or a list of floating points that will be used to set nodata values 
                to the raster map.

        Returns:
            tuple: A tuple containing a rasterio.DatasetReader and a numpy.array.
        """
        with rio.open(self.path) as src:
            array = src.read(1).astype("float")
            if isinstance(nodata, float):
                nodata = [nodata]
            for value in nodata:
                array[array == value] = np.nan
        return src, array

    def plot(self,
             cmap='Greys_r',
             nodata: Union[float, list[float]] = -32768.0,
             ax: plt.Axes = None,
             cbar=True,
             **kwargs) -> GeoAxes:
        """This method can be used to plot rasters.

        Args:
            cmap: A matplotlib colormap. Defaults to 'Greys_r'. For more details check the matplotlib
                documentation.
            nodata: A float or a list of floating points that will be used to set nodata values
                to the raster map.
            ax: A matplotlib axes object.
            cbar: Whether to add a colorbar or not.
            **kwargs: Options to pass to the 'imshow' method of matplotlib.

        Returns:
            GeoAxes: A cartopy GeoAxes object.
        """
        src, array = self._read_raster(nodata=nodata)
        crs = str(src.crs).split(':')[-1]
        left, bottom, right, top = src.bounds
        proj = ccrs.epsg(crs)
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(projection=proj)
        else:
            fig = ax.figure
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
        return ax

    def histogram(self,
                  nodata: Union[float, list] = -32768.0,
                  ax=None,
                  **kwargs) -> plt.Axes:
        """This method can be used to plot a histogram of raster.
        
        Args:
            cmap: A matplotlib colormap. For more details check the matplotlib
                documentation.
            nodata: A float or a list of floating points that will be used to set nodata values
                to the raster map.
            ax: A matplotlib axes object. Defaults to None.
            **kwargs: Options to pass to the 'hist' method of matplotlib.

        Returns:
            plt.Axes: A matplotlib axes object.
        """
        _, array = self._read_raster(nodata=nodata)
        array = array.flatten()
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot()
        ax.hist(
            array,
            **kwargs
        )
        return ax
    
    def to_numpy(self,
                 nodata: Union[float, list] = -32768.0,):
        return (
            self._read_raster(nodata=nodata)[1]
        )



@define
class Vector:
    """A georeferenced vector object.
    The class is currently unstable and untested.

    Parameters
    ----------
    path: The file path of the vector.

    Methods
    ----------
    plot: Plots the vector object. Returns an 'Axes' object.
    """

    path: str

    def _read_vector(self) -> gpd.GeoDataFrame:
        return gpd.read_file(self.path)
    
    def plot(self, ax=None, **kwargs) -> plt.Axes:
        file = self._read_vector()
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot()
        file.plot(
            ax=ax,
            **kwargs
        )
        return ax
