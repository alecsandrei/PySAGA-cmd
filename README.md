# PySAGA-cmd
PySAGA-cmd is a simple way of running SAGA GIS tools using Python.

## How to download

Binary installers for the latest released version are available at the [Python Package Index (PyPI)](https://pypi.org/project/PySAGA-cmd/).
```sh
pip install PySAGA-cmd
```

## How to use the package
For information on how to use the package, I recommend looking at the [notebooks](https://github.com/alecsandrei/PySAGA-cmd/tree/master/examples/notebooks) inside the examples folder on the Github page.


# TODO before the launch of v1.0.7.

- [x] Remove all dependencies. All the dependencies will be turned into extra dependencies. Switch from attrs to dataclasses.
- [x] Write simple tests.
- [ ] Add an extra feature: **build your own tools**.
- [ ] Use a tool like zest.releaser to release v1.0.7.
- [x] Make objects more pythonic (add truediv to access tools faster for example instead of less nicer getter methods).