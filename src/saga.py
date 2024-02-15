"""Contains the main functionalities of the PySAGA-cmd package."""

from __future__ import annotations

import os
import time
import shutil
import tempfile
from typing import (
    Union,
    Optional,
    Protocol,
    Sequence,
    Self,
    Any,
    TYPE_CHECKING,
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
from functools import cache

from src.utils import (
    check_is_file,
    check_is_executable,
    get_sagacmd_default,
    infer_file_extension,
)


if TYPE_CHECKING:
    from objects import (  # type: ignore
        Raster,
        Vector
    )

PathLike = Union[str, os.PathLike]


@cache
def temp_dir():
    return Path(tempfile.mkdtemp())


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

    saga_cmd_path: PathLike

    def __init__(self, saga_cmd_path: Optional[PathLike] = None) -> None:
        if saga_cmd_path is None:
            saga_cmd_path = get_sagacmd_default()
        elif not isinstance(saga_cmd_path, Path):
            saga_cmd_path = Path(os.fspath(saga_cmd_path))
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
class Parameters(dict[str, str]):
    """The SAGA GIS tool parameters.

    This object inherits from UserDict and therefore cand be
    used as a dictionary.

    Parameters
    ----------
    **kwargs: The tool parameters as keyword arguments. For example,
      'elevation=/path/to/raster' could be a keyword argument.

    Examples
    ---------
    >>> params = Parameters(elevation='path/to/raster',
    ...                     grid='path/to/grid',
    ...                     method=0)
    >>> print(params)
    -ELEVATION='path/to/elevation' -GRID='path/to/grid' -METHOD='0'
    """

    def __init__(self, **kwargs: SupportsStr) -> None:
        super().__init__()
        for param, value in kwargs.items():
            value = str(value)
            self[param] = str(value)

    def __str__(self):
        return ' '.join(format_parameters(self))

    def __repr__(self):
        return super().__repr__()

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, name, value):
        self[name] = value

    def _params_formatted(self):
        return (param for param in format_parameters(self))


def format_parameters(parameters: Parameters) -> list[str]:
    """Used to format the parameters as required by SAGAGIS."""
    params = []
    param_format = '-{PARAM}={value}'
    for param, value in parameters.items():
        params.append(param_format.format(PARAM=param.upper(), value=value))
    return params


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
    saga_cmd: The file path to the 'saga_cmd' file. For information
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
        saga_cmd: Optional[Union[PathLike, SAGACMD]] = None,
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
    def temp_dir(self) -> Path:
        return temp_dir()

    @property
    def temp_files(self):
        return list(temp_dir().iterdir())

    def temp_dir_cleanup(self):
        files = [*self.temp_dir.iterdir()]
        shutil.rmtree(self.temp_dir)
        print('The following files were removed:')
        for file in files:
            assert not file.exists()
            print(file)

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
    saga_cmd: The file path to the 'saga_cmd' file. For information
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
        saga_cmd: Optional[Union[PathLike, SAGACMD]] = None,
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
    """Describes a SAGA GIS tool.f

    Parameters
    ----------
    library: The SAGA GIS library object.
    tool: The tool name.
    saga_cmd: The file path to the 'saga_cmd' file. For information
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
        saga_cmd: Optional[Union[PathLike, SAGACMD]] = None,
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

    def __call__(self, **kwargs: SupportsStr) -> Self:
        """Uses keyword argument to define parameters and to set attrs.

        Besides setting attributes and defining the parameters for
        the tool, it also replaces 'temp' values with a temporary
        file location.
        """
        if self.parameters:
            for param in self.parameters:
                # Delete all previous parameter attributes.
                delattr(self, param)
        for param, value in kwargs.items():
            value = str(value)
            val_as_path = Path(value)
            if val_as_path.stem == 'temp':
                suffix = val_as_path.suffix
                unix = str(time.time()).split('.')[0]
                kwargs[param] = (
                    temp_dir() / f'{param}_{unix}{suffix}'
                ).as_posix()
            setattr(self, param, kwargs[param])
        self.parameters = Parameters(**kwargs)
        return self

    def __getattr__(self, name: str) -> Any: pass

    @property
    def command(self) -> Command:
        return (
            Command(self.saga_cmd,
                    self.flag,
                    self.library,
                    self.tool,
                    *self.parameters._params_formatted())
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

    def __or__(self, tool: Tool) -> Pipeline:
        return Pipeline(self) | (tool)

    def run_command(self, **kwargs: SupportsStr) -> Output:
        if kwargs:
            self(**kwargs)
        for param, value in self.parameters.items():
            value_as_path = Path(value)
            if value_as_path.parent.exists() and not value_as_path.suffix:
                value = ''.join(
                    [value, infer_file_extension(value_as_path)]
                )
                self.parameters[param] = value
        completed_process = self.command.execute()
        return Output(completed_process, self.parameters)


@dataclass
class Pipeline:
    tools: list[Tool]

    def __init__(
        self,
        tool: Tool
    ):
        self.tools = [tool]

    def __or__(self, tool: Tool) -> Self:
        self.tools.append(tool)
        return self

    def execute(self, verbose=False) -> list[Output]:
        """Executes the tools in the pipeline.

        Args:
            verbose: Wether or not to print the output text after
              the execution of each tool.
        """
        outputs = []
        for tool in self.tools:
            output = tool.run_command()
            if verbose:
                lines = output.text.split('\n')
                cleaned_lines = [line for line in lines
                                 if '%' not in line and line]
                print('\n'.join(cleaned_lines))
            outputs.append(output)
        return outputs

    def __str__(self):
        string = []
        for tool in self.tools:
            string.extend([tool.library, ' ', tool, '\n'])
            string.extend(['    ', tool.parameters, '\n'])
            string.extend(['-'*10, '\n'])
        return ''.join(str(element) for element in string[:-3])


class PipelineError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


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
        return ' '.join(f'"{arg}"' for arg in self.args)

    def execute(self) -> subprocess.CompletedProcess:
        return (
            subprocess.run(self.args, capture_output=True, text=True)
        )


@dataclass
class Output:
    """The output of the child process.

    Parameters
    ----------
    completed_process: A 'CompletedProcess' object that was returned by
      a command execution.
    parameters: The 'Parameters' object passed to the 'Command' object.

    Attributes
    ----------
    text: The 'stdout' attribute of the 'CompletedProcess' object as string.

    Methods
    ----------
    get_raster: Takes as input a parameter. Check the 'parameters' attribute
      of this class to see available parameters. Returns a 'Raster' object
      or a list of them.
    get_vector: Takes as input a parameter. Check the 'parameters' attribute
      of this class to see available parameters. Returns a 'Vector' object
      or a list of them.
    """

    completed_process: subprocess.CompletedProcess
    parameters: Parameters = field(default_factory=Parameters)
    text: str = field(init=False)

    def __post_init__(self) -> None:
        self.text = str(self.completed_process.stdout)

    def get_raster(
        self,
        parameters: Union[Sequence[str], str]
    ) -> list[Raster]:

        from objects import Raster
        if isinstance(parameters, str):
            parameters = [parameters]
        return (
            [Raster(v) for k, v in self.parameters.items()
             if k in parameters]
        )

    def get_vector(
        self,
        parameters: Union[Sequence[str], str]
    ) -> list[Vector]:

        from objects import Vector

        if isinstance(parameters, str):
            parameters = [parameters]
        return (
            [Vector(v) for k, v in self.parameters.items()
             if k in parameters]
        )
