"""Plotting and other utilities for raster and vector objects."""

from __future__ import annotations

import os
from pathlib import Path
from typing import (
    Union,
    Iterable,
    SupportsFloat,
    Optional,
    TYPE_CHECKING
)
from dataclasses import dataclass

from PySAGA_cmd.utils import (
   infer_file_extension,
   depends
)

if TYPE_CHECKING:
    import numpy as np
    import rasterio as rio  # type: ignore
    import matplotlib.axes as axes


HERE = Path(__file__).parent

PathLike = Union[str, os.PathLike]


@dataclass
class Raster:
    """A raster object.

    Parameters
    ----------
    path: The file path of the raster image.

    Methods
    ----------
    plot: Plots the raster file. Returns a axes.Axes object.
    hist: Plots a hist of the raster file. Returns an axes.Axes object.
    to_numpy: Returns the Raster object as a np.array.
    """

    def __init__(self, path: PathLike):
        self.path = Path(path)
        if not self.path.suffix:
            self.path = infer_file_extension(self.path)

    def __str__(self):
        return os.fspath(self.path)

    def _read_raster(
        self,
        nodata: Union[SupportsFloat, Iterable[SupportsFloat]] = -32768.0
    ) -> tuple[rio.DatasetReader, np.ndarray]:
        """This method will be used to read raster objects using rasterio.

        Args:
            nodata: A float or an iterable of floats that will be masked.

        Returns:
            tuple: A tuple containing a rasterio.DatasetReader
              and a numpy.array.
        """
        import rasterio as rio
        import numpy as np

        with rio.open(self.path) as src:
            array = src.read(1).astype("float")
            if isinstance(nodata, SupportsFloat):
                nodata = [nodata]
            for value in nodata:
                array[array == value] = np.nan
        return src, array

    @depends
    def plot(
        self,
        cmap='Greys_r',
        nodata: Union[SupportsFloat, Iterable[SupportsFloat]] = -32768.0,
        ax: Optional[axes.Axes] = None,
        cbar=True,
        cbar_kwargs: Optional[dict] = None,
        **kwargs
    ) -> axes.Axes:
        """This method can be used to plot rasters.

        Args:
            cmap: A matplotlib colormap. Defaults to 'Greys_r'.
              For more details check the matplotlib documentation.
            nodata: A float or an iterable of floats that will be used to
              set nodata values to the raster map.
            ax: A matplotlib.axes.Axes object.
            cbar: Whether to add a colorbar or not.
            cbar_kwargs: Keyword arguments to pass to plt.colorbar.
            **kwargs: Keyword arguments to pass to the axes.Axes.imshow.

        Returns:
            matplotlib.axes.Axes: A matplotlib.axes.Axes object.
        """
        import matplotlib.pyplot as plt
        from mpl_toolkits.axes_grid1 import make_axes_locatable  # type: ignore

        src, array = self._read_raster(nodata=nodata)
        left, bottom, right, top = src.bounds
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot()
        else:
            if ax.figure is None:
                raise NotImplementedError(
                    'The provided "ax" argument does not have a figure.'
                )
            fig = ax.figure  # type: ignore
        im = ax.imshow(
                array,
                cmap=cmap,
                extent=(left, right, bottom, top),
                **kwargs)
        if cbar:
            assert fig is not None
            if cbar_kwargs is None:
                cbar_kwargs = {}
            if 'cax' not in cbar_kwargs:
                cbar_kwargs['cax'] = (make_axes_locatable(ax)
                                      .append_axes("right", size="5%",
                                                   pad=0.05))
            plt.colorbar(im, **cbar_kwargs)
        return ax

    @depends
    def hist(
        self,
        nodata: Union[SupportsFloat, Iterable[SupportsFloat]] = -32768.0,
        ax: Optional[axes.Axes] = None,
        **kwargs
    ) -> axes.Axes:
        """This method can be used to plot a hist of raster.

        Args:
            cmap: A matplotlib colormap. For more details check the matplotlib
              documentation.
            nodata: A float or a list of floating points that will be
              used to set nodata values to the raster map.
            ax: A matplotlib.axes.Axes object. Defaults to None.
            **kwargs: Options to pass to the 'hist' method of matplotlib.

        Returns:
            matplotlib.axes.Axes: A matplotlib.axes.Axes object.
        """
        import matplotlib.pyplot as plt

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

    @depends
    def to_numpy(
        self,
        nodata: Union[SupportsFloat, Iterable[SupportsFloat]] = -32768.0
    ):
        """Returns the raster as a numpy array."""
        return (
            self._read_raster(nodata=nodata)[1]
        )


@dataclass
class Vector:
    """A georeferenced vector object.

    TODO: add more functionality to this class.

    Parameters
    ----------
    path: The file path of the vector file.

    Methods
    ----------
    plot: Plots the vector object.
    """

    def __init__(self, path: PathLike):
        self.path = Path(path)
        if not self.path.suffix:
            self.path = infer_file_extension(self.path)

    def __str__(self):
        return os.fspath(self.path)

    def _read_vector(self):
        import geopandas as gpd  # type: ignore
        return gpd.read_file(self.path)

    @depends
    def plot(
        self,
        ax: Optional[axes.Axes] = None,
        **kwargs
    ) -> axes.Axes:
        """Plots the vector object."""
        import matplotlib.pyplot as plt

        file = self._read_vector()
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot()
        file.plot(
            ax=ax,
            **kwargs
        )
        return ax


def get_sample_dem() -> Raster:
    """Get a sample DEM of an area in North-Eastern Romania."""
    return Raster(HERE / '../assets/DEM_30m.tif')
