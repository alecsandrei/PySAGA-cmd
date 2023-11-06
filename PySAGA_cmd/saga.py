"""Contains the main functionalities of the PySAGA-cmd package."""

from __future__ import annotations

import subprocess
from typing import Type, Union
from attrs import define, field
from abc import ABC, abstractmethod

from PySAGA_cmd._util import (
    check_is_file,
    check_is_executable,
    get_sagacmd_default
)
from PySAGA_cmd._plot import (
    Raster,
    Vector
)


@define
class SAGACMD:
    """The saga_cmd file object.

    Parameters
    ----------
    sagacmd: The file path to the 'saga_cmd' file. For information on where to find it, 
        check the following link https://sourceforge.net/projects/saga-gis/files/SAGA%20-%20Documentation/Tutorials/Command_Line_Scripting/.

    Raises
    ----------
    IsADirectoryError: When a directory path was provided instead of a file path.
    ValueError: When the provided file path does not link to a file.
    """

    sagacmd: str = field(default=None)

    def __attrs_post_init__(self) -> None:
        if self.sagacmd is None:
            self.sagacmd = get_sagacmd_default()
        check_is_file(self.sagacmd)
        check_is_executable(self.sagacmd)

@define
class Flag:
    """Flag that can be run with the command.
    
    Parameters
    ----------
    flag: {'help', 'version', 'batch', 'docs', 'cores'} The flag to use when running the command.
    """

    flag: str = field(default=None)

    def __attrs_post_init__(self) -> None:
        if self.flag:
            self.flag = '--' + self.flag

@define
class Parameters:
    """The SAGA GIS tool parameters.
    
    Parameters
    ----------
    kwargs: The tool parameters to pass to 'Tool.run_command' as keyword arguments.
        All of the arguments should be strings.

    Attributes
    ----------
    parameters: The 'kwargs' parameter formated as a tuple ready to be
        unpacked by the 'Command.run_command' method.

    Examples
    ---------
    >>> params = Parameters(kwargs={'elevation': 'path/to/elevation',
    ...                             'grid': 'path/to/grid',
    ...                             'method': '0'}
    >>> print(params.parameters)
    ('-ELEVATION', 'path/to/elevation', '-GRID', 'path/to/grid', '-METHOD', '0')
    """

    kwargs: dict = field(factory=dict)
    parameters: tuple[str] = field(default=None, init=False)

    def __attrs_post_init__(self) -> None:
        self.parameters = tuple()
        if self.kwargs:
            for k, v in self.kwargs.items():
                self.parameters += (f'-{k.upper()}', )
                self.parameters += (v, )

@define
class Executable(ABC):
    """Describes an object that is executable."""

    sagacmd: Union[SAGACMD, str, None] = field(default=None)
    _flag: Flag = field(default=Flag())

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

@define
class SAGA(Executable):
    """The SAGA GIS main program as an object.
    
    Parameters
    ----------
    sagacmd: The file path to the 'saga_cmd' file. For information on where to find it,
        check the following link https://sourceforge.net/projects/saga-gis/files/SAGA%20-%20Documentation/Tutorials/Command_Line_Scripting/.

    Attributes
    ----------
    command: The 'Command' object which will be used to execute the 'run_command' method.
    flag: {'help', 'version', 'batch', 'docs', 'cores'} The flag to use when running the command.
        This attribute has a getter, setter and a deleter.
    
    Methods
    -------
    get_library: Takes as input a SAGA GIS library name (e.g 'ta_morphometry')
        and returns a 'Library' object.
    get_tool: Takes as input a library tool name (e.g '0')
        and returns a 'Tool' object.
    run_command: Executes the child process. To see the command that will be executed,
        check the 'command' attribute of this class.
    """

    def __attrs_post_init__(self) -> None:
        if isinstance(self.sagacmd, str):
            self.sagacmd = SAGACMD(self.sagacmd)
        elif self.sagacmd is None:
            self.sagacmd = SAGACMD()

    @property
    def command(self) -> Command:
        return (
            Command(self.sagacmd.sagacmd,
                    self.flag.flag)
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
        return (
            Library(sagacmd=self.sagacmd, flag=self.flag, library=library)
        )
    
    def get_tool(self, library: str, tool: str) -> Tool:
        library = self.get_library(library)
        return (
            Tool(sagacmd=self.sagacmd, flag=self.flag, library=library, tool=tool)
        )

    def run_command(self) -> Output:
        return (
            Output(self.command.execute())
        )

@define(kw_only=True)
class Library(Executable):
    """A SAGA GIS library.

    Parameters
    ----------
    library: the SAGA GIS library name

    Attributes
    ----------
    command: The 'Command' object which will be used to execute the 'run_command' method.
    flag: {'help', 'version', 'batch', 'docs', 'cores'} The flag to use when running the command.
        This attribute has a getter, setter and a deleter.
    
    Methods
    -------
    get_library: Takes as input a SAGA GIS library name (e.g 'ta_morphometry')
        and returns a 'Library' object.
    get_tool: Takes as input a library tool name (e.g. '0')
        and returns a 'Tool' object.
    run_command: Executes the child process. To see the command that will be executed,
        check the 'command' attribute of this class.
    """

    library: str

    @property
    def command(self) -> Command:
        return (
            Command(self.sagacmd.sagacmd,
                    self.flag.flag,
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
        return (
            Tool(sagacmd=self.sagacmd, flag=self.flag, library=self, tool=tool)
        )

    def run_command(self) -> Output:
        return (
            Output(self.command.execute())
        )
        
@define(kw_only=True)
class Tool(Executable):
    """A SAGA GIS tool.

    Parameters
    ----------
    library: The 'Library' object where the tool resides in.
    tool: The name of the tool (e.g. '0')
    parameters : Takes as input a 'Parameters' object. Initializing this parameter is not necessary and instead you can
        pass keyword arguments to the 'run_command' method.

    Attributes
    ----------
    command: The 'Command' object which will be used to execute the 'run_command' method.
    flag: {'help', 'version', 'batch', 'docs', 'cores'} The flag to use when running the command.
        This attribute has a getter, setter and a deleter.
    
    Methods
    -------
    get_library: Takes as input a SAGA GIS library name (e.g 'ta_morphometry')
        and returns a 'Library' object.
    get_tool: Takes as input a library tool name (e.g '0')
        and returns a 'Tool' object.
    run_command: Takes as input multiple keyword arguments which will be used to construct
        a 'Parameters' object. Executes the child process. To see the command that will be executed
        (without the keyword arguments), check the 'command' attribute of this class.
    """

    library: Library
    tool: str
    parameters: Type['Parameters'] = field(default=Parameters())

    @property
    def command(self) -> Command:
        # the 'parameters' attribute from the Parameters class needs to be unpacked
        return (
            Command(self.sagacmd.sagacmd,
                    self.flag.flag,
                    self.library.library,
                    self.tool,
                    *self.parameters.parameters)
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
        if len(kwargs) != 0:
            self.parameters = Parameters(kwargs)
        completed_process = self.command.execute()
        return Output(completed_process, self.parameters)

@define(init=False)
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

    command: list[str] = field(default=None, init=False)

    def __init__(self, *args) -> None:
        self.command = [command for command in args
                        if command]
    
    def execute(self) -> str:
        return (
            subprocess.run(self.command, capture_output=True, text=True)
        )
    
@define
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
    
    