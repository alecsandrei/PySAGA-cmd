"""Contains the main functionalities of the PySAGA-cmd package."""

from __future__ import annotations

import os
from typing import (
    Union,
    Optional,
    Protocol,
    Mapping
)
from pathlib import Path
import subprocess
from abc import (
    ABC,
    abstractmethod
)
from dataclasses import (
    dataclass,
    field
)

from src.utils import (
    check_is_file,
    check_is_executable,
    get_sagacmd_default,
)
from src.plot import (
    Raster,
    Vector
)


SAGACMDPath = Union[str, os.PathLike]


@dataclass
class SAGACMD:
    """The saga_cmd file object.

    Parameters
    ----------
    saga_cmd_path: The file path to the 'saga_cmd' file. For information
      on where to find it, check the following link:
      https://sourceforge.net/projects/saga-gis/files/SAGA%20-%20Documentation/Tutorials/Command_Line_Scripting/.

    Raises
    ----------
    PathDoesNotExist: If 'saga_cmd_path' does not point to a valid
      system file or directory.
    IsADirectoryError: If 'saga_cmd_path' points to a directory
      instead of a file.
    FIleNotFoundError: If 'saga_cmd_path' does not point to an existing
      file
    SubprocessError: If 'saga_cmd_path' can not be executed.
    OSError: If 'saga_cmd_path' can not be executed.
    """

    saga_cmd_path: SAGACMDPath

    def __init__(self, saga_cmd_path: Optional[SAGACMDPath] = None) -> None:
        if saga_cmd_path is None:
            saga_cmd_path = get_sagacmd_default()
        elif not isinstance(saga_cmd_path, Path):
            saga_cmd_path = Path(saga_cmd_path)
        self.saga_cmd_path = saga_cmd_path
        check_is_file(self.saga_cmd_path)
        check_is_executable(self.saga_cmd_path)

    def __str__(self):
        return os.fspath(self.saga_cmd_path)

    def __fspath__(self):
        return str(self)


@dataclass
class Flag:
    """Describes a flag object that can be used when running commands.

    Parameters
    ----------
    flag: The flag to use when running the command. Examples of flags include:
      'cores=8', 'flags=s', 'help', 'version' etc. Check the SAGA GIS
      documentation if you want to find out more about flags.
    """

    flag: Optional[str] = field(default=None)

    def __str__(self):
        if self.flag is None:
            return ''
        if isinstance(self.flag, str) and not self.flag.startswith('--'):
            return ''.join(['--' + self.flag])
        return self.flag

    def __bool__(self):
        return self.flag is not None

    def __eq__(self, other):
        return str(self) == other


@dataclass
class Parameters:
    """The SAGA GIS tool parameters.

    Parameters
    ----------
    **kwargs: The tool parameters as keyword arguments. For example,
      'elevation=/path/to/raster' could be a keyword argument.

    Attributes
    ----------
    params: The parameters of the tool, formatted.

    Examples
    ---------
    >>> params = Parameters(elevation='path/to/raster',
    ...                     grid='path/to/grid',
    ...                     method=0)
    >>> print(params)
    -ELEVATION='path/to/elevation' -GRID='path/to/grid' -METHOD='0'
    """

    params: list[str]

    def __init__(self, **kwargs: Mapping[str, SupportsStr]) -> None:
        self.params = []
        param = '-{K}={v}'
        if kwargs:
            for k, v in kwargs.items():
                self.params.append(
                    param.format(K=k.upper(), v=str(v))
                )

    def __iter__(self):
        return (param for param in self.params)

    def __getitem__(self, idx: int):
        return self.params[idx]

    def __str__(self):
        return ' '.join(self.params)


@dataclass
class Executable(ABC):
    """Describes an object that is executable."""

    saga_cmd: SAGACMD
    _flag: Flag

    @property
    @abstractmethod
    def command(self):
        """Gets the current command."""

    @property
    @abstractmethod
    def flag(self):
        """Gets the current flag."""

    @flag.setter
    def flag(self):
        """Sets the current flag."""

    @flag.deleter
    def flag(self):
        """Deletes the current flag."""

    @abstractmethod
    def run_command(self) -> Output:
        """Runs the 'execute' method of a Command type object."""


@dataclass
class SAGA(Executable):
    """The SAGA GIS main program as an object.

    Parameters
    ----------
    saga_cmd_path: The file path to the 'saga_cmd' file. For information
      on where to find it, check the following link:
      https://sourceforge.net/projects/saga-gis/files/SAGA%20-%20Documentation/Tutorials/Command_Line_Scripting/.
    flag: The flag to use when running the command. For more details, check
      the docstrings for the 'Flag' object in this module.

    Attributes
    ----------
    saga_cmd: A 'SAGACMD' object describing the 'saga_cmd' executable.
    flag: A 'Flag' object describing the flag that will be used when
      running the command.
    command: The command that will be executed with the 'run_command' method.

    Methods
    -------
    get_library: Takes as input a SAGA GIS library name (e.g 'ta_morphometry')
      and returns a 'Library' object.
    get_tool: Takes as input a library tool name (e.g '0')
      and returns a 'Tool' object.
    run_command: Executes the command. To see the command that will be
      executed, check the 'command' property of this class.
    """

    def __init__(
        self,
        saga_cmd: Optional[Union[SAGACMDPath, SAGACMD]] = None,
        flag: Optional[Union[str, Flag]] = None
    ) -> None:
        if not isinstance(saga_cmd, SAGACMD):
            saga_cmd = SAGACMD(saga_cmd)
        if not isinstance(flag, Flag):
            flag = Flag(flag)
        self.saga_cmd = saga_cmd
        self._flag = flag

    def __truediv__(self, library: Union[Library, str]):
        if isinstance(library, str):
            return self.get_library(library=library)
        return library

    @property
    def command(self) -> Command:
        return (
            Command(self.saga_cmd,
                    self.flag)
        )

    @property
    def flag(self) -> Flag:
        return self._flag

    @flag.setter
    def flag(self, flag: Union[str, None]) -> None:
        self._flag = Flag(flag)

    @flag.deleter
    def flag(self) -> None:
        self._flag = Flag()

    def get_library(self, library: str) -> Library:
        """Get a SAGA GIS Library object.

        Args:
            library: The library name. For example, 'ta_morphometry'.
              Check the SAGA GIS documentation for more details:
              https://saga-gis.sourceforge.io/saga_tool_doc/9.3.1/index.html

        Returns:
            Library: An object describing the SAGA GIS library.
        """
        return (
            Library(saga_cmd=self.saga_cmd, flag=self.flag, library=library)
        )

    def get_tool(self, library: str, tool: str) -> Tool:
        """Get a SAGA GIS Tool object.

        Args:
            library: The library name. For example, 'ta_morphometry'.
            tool: The name for the tool inside the library. For more
              details, check the SAGA GIS documentation:
              https://saga-gis.sourceforge.io/saga_tool_doc/9.3.1/index.html

        Returns:
            Tool: An object describing the SAGA GIS tool.
        """
        library_ = self.get_library(library)
        return (
            Tool(library=library_,
                 tool=tool,
                 saga_cmd=self.saga_cmd,
                 flag=self.flag)
        )

    def run_command(self) -> Output:
        return (
            Output(self.command.execute())
        )


@dataclass
class Library(Executable):
    """Describes a SAGA GIS library.

    Parameters
    ----------
    library: the SAGA GIS library name.
    saga_cmd_path: The file path to the 'saga_cmd' file. For information
      on where to find it, check the following link:
      https://sourceforge.net/projects/saga-gis/files/SAGA%20-%20Documentation/Tutorials/Command_Line_Scripting/.
    flag: The flag to use when running the command. For more details, check
      the docstrings for the 'Flag' object in this module.

    Attributes
    ----------
    saga_cmd: A 'SAGACMD' object describing the 'saga_cmd' executable.
    flag: A 'Flag' object describing the flag that will be used when
      running the command.
    command: The command that will be executed with the 'run_command' method.
    library: The library name.

    Methods
    -------
    get_tool: Takes as input a library tool name (e.g. '0')
      and returns a 'Tool' object.
    run_command: Executes the command. To see the command that will be
      executed, check the 'command' property of this class.
    """

    library: str

    def __init__(
        self,
        library: str,
        saga_cmd: Optional[Union[SAGACMDPath, SAGACMD]] = None,
        flag: Optional[Union[str, Flag]] = None
    ) -> None:
        if not isinstance(saga_cmd, SAGACMD):
            saga_cmd = SAGACMD(saga_cmd)
        if not isinstance(flag, Flag):
            flag = Flag(flag)
        self.saga_cmd = saga_cmd
        self._flag = flag
        self.library = library

    def __str__(self):
        return self.library

    def __truediv__(self, tool: Union[Tool, str]):
        if isinstance(tool, str):
            return self.get_tool(tool=tool)
        return tool

    @property
    def command(self) -> Command:
        return (
            Command(self.saga_cmd,
                    self.flag,
                    self.library)
        )

    @property
    def flag(self) -> Flag:
        return self._flag

    @flag.setter
    def flag(self, flag: Union[str, None]) -> None:
        self._flag = Flag(flag)

    @flag.deleter
    def flag(self) -> None:
        self._flag = Flag()

    def get_tool(self, tool: str) -> Tool:
        """Get a SAGA GIS Tool object.

        Args:
            tool: The name for the tool inside the library. For more
              details, check the SAGA GIS documentation:
              https://saga-gis.sourceforge.io/saga_tool_doc/9.3.1/index.html

        Returns:
            Tool: An object describing the SAGA GIS tool.
        """
        return (
            Tool(saga_cmd=self.saga_cmd,
                 flag=self.flag,
                 library=self,
                 tool=tool)
        )

    def run_command(self) -> Output:
        return (
            Output(self.command.execute())
        )


@dataclass
class Tool(Executable):
    """Describes a SAGA GIS tool.

    Parameters
    ----------
    library: The SAGA GIS library object.
    tool: The tool name.
    saga_cmd_path: The file path to the 'saga_cmd' file. For information
      on where to find it, check the following link:
      https://sourceforge.net/projects/saga-gis/files/SAGA%20-%20Documentation/Tutorials/Command_Line_Scripting/.
    flag: The flag to use when running the command. For more details, check
      the docstrings for the 'Flag' object in this module.

    Attributes
    ----------
    saga_cmd: A 'SAGACMD' object describing the 'saga_cmd' executable.
      running the command.
    flag: A 'Flag' object describing the flag that will be used when
    command: The command that will be executed with the 'run_command' method.
    library: The SAGA GIS library object.
    tool: The tool name.

    Methods
    -------
    run_command: Takes as input keyword arguments which will be
      used to construct a 'Parameters' object. Example of a keyword
      argument would be 'elevation=/path/to/raster. To see the command
      that will be executed, check the 'command' attribute of this class.
    """

    library: Library
    tool: str
    parameters: Parameters

    def __init__(
        self,
        library: Library,
        tool: str,
        saga_cmd: Optional[Union[SAGACMDPath, SAGACMD]] = None,
        flag: Optional[Union[str, Flag]] = None
    ) -> None:
        if not isinstance(saga_cmd, SAGACMD):
            saga_cmd = SAGACMD(saga_cmd)
        if not isinstance(flag, Flag):
            flag = Flag(flag)
        self.saga_cmd = saga_cmd
        self._flag = flag
        self.library = library
        self.tool = tool
        self.parameters = Parameters()

    def __str__(self):
        return self.tool

    @property
    def command(self) -> Command:
        return (
            Command(self.saga_cmd,
                    self.flag,
                    self.library,
                    self.tool,
                    *self.parameters)
        )

    @property
    def flag(self) -> Flag:
        return self._flag

    @flag.setter
    def flag(self, flag: Union[str, None]) -> None:
        self._flag = Flag(flag)

    @flag.deleter
    def flag(self) -> None:
        self._flag = Flag()

    def run_command(self, **kwargs) -> Output:
        if kwargs:
            self.parameters = Parameters(**kwargs)
        completed_process = self.command.execute()
        return Output(completed_process, self.parameters)


class SupportsStr(Protocol):
    def __str__(self) -> str:
        ...


@dataclass
class Command:
    """The commands to be executed.

    Attributes
    ----------
    command: The command to be passed to the 'subprocess.run' function.

    Methods
    ----------
    execute: Passes the 'command' attribute to the 'subprocess.run' function
        and executes the 'subprocess.run' function.
    """

    args: list[str] = field(default_factory=list, init=False)

    def __init__(self, *args: SupportsStr) -> None:
        self.args = [str(arg) for arg in args if arg]

    def __iter__(self):
        return (arg for arg in self.args)

    def __getitem__(self, idx: int):
        return self.args[idx]

    def __str__(self):
        return ' '.join(arg for arg in self.args)

    def execute(self) -> subprocess.CompletedProcess:
        return (
            subprocess.run(self.args, capture_output=True, text=True)
        )


@dataclass
class Output:
    """The output of the child process.

    Parameters
    ----------
    completed_process: A 'CompletedProcess' object that was returned by the 'subprocess.run' function.
    parameters: An optional 'Parameters' object.

    Attributes
    ----------
    text: The 'stdout' attribute of the 'CompletedProcess' object.

    Methods
    ----------
    get_raster: Takes as input a parameter passed to the 'Tool.run_command' method (e.g. 'dem' or 'elevation'). Check
        the 'parameters' attribute of this class to see available parameters.
        Returns a list of 'Raster' objects or a 'Raster' object.
    get_vector: Takes as input a parameter passed to the 'Tool.run_command' method (e.g. 'dem' or 'elevation'). Check
        the 'parameters' attribute of this class to see available parameters.
        Returns a list of 'Vector' objects or a 'Vector' object.
    """

    completed_process: subprocess.CompletedProcess
    parameters: Parameters = field(default=None)
    text: str = field(init=False)

    def __attrs_post_init__(self) -> None:
        self.text = self.completed_process.stdout

    def get_raster(self, parameters: Union[list[str], str]) -> Union[list[Raster], Raster]:
        if isinstance(parameters, list):
            return [Raster(self.parameters.kwargs[parameter])
                    for parameter in parameters]
        return Raster(self.parameters.kwargs[parameters])
    def get_vector(self, parameters: Union[list[str], str]) -> Union[list[Vector], Vector]:
        if isinstance(parameters, list):
            return [Vector(self.parameters.kwargs[parameter])
                    for parameter in parameters]
        return Vector(self.parameters.kwargs[parameters])


if __name__ == '__main__':
    dem = './data/example_input/DEM_30m.tif'
    shade = './data/example_output/shade.tif'
    saga_env = SAGA(sagacmd='/usr/local/bin/saga_cmd')
    saga_lib = saga_env.get_library(library='ta_lighting')
    saga_tool = saga_lib.get_tool(tool='0')
    output = saga_tool.run_command(elevation=dem,
                                   shade=shade,
                                   method='2')
    print(output.text)
    output.get_raster(['shade', 'elevation'])[0].plot()
    # use plt.show to visualize
