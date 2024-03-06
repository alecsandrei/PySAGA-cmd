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
    Iterable,
    TypeVar,
    Any,
    runtime_checkable,
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

from PySAGA_cmd.utils import (
    check_is_file,
    check_is_executable,
    get_sagacmd_default,
    infer_file_extension,
    dynamic_print,
)


if TYPE_CHECKING:
    from objects import (  # type: ignore
        Raster,
        Vector
    )


def temp_dir():
    return Path(tempfile.mkdtemp())


PathLike = Union[str, os.PathLike]


# TODO: implement some sort of searching for the 'saga_cmd' file.


@runtime_checkable
class SupportsStr(Protocol):
    def __str__(self) -> str:
        ...


@dataclass
class SAGACMD:
    """The saga_cmd file object.

    If the path parameter is not provided, a default value
    will be set according to the user's platform.

    Parameters
    ----------
    path: The file path to the 'saga_cmd' file. For information
      on where to find it, check the following link:
      https://sourceforge.net/projects/saga-gis/files/SAGA%20-%20Documentation/Tutorials/Command_Line_Scripting/.

    Raises
    ----------
    PathDoesNotExist: If 'path' does not point to a valid
      system file or directory.
    IsADirectoryError: If 'path' points to a directory
      instead of a file.
    FIleNotFoundError: If 'path' does not point to an existing
      file
    SubprocessError: If 'path' can not be executed.
    OSError: If 'path' can not be executed.
    """

    path: Optional[PathLike] = field(default=None)

    def __post_init__(self) -> None:
        if self.path is None:
            self.path = get_sagacmd_default()
        elif not isinstance(self.path, Path):
            self.path = Path(self.path)
        check_is_file(self.path)
        check_is_executable(self.path)

    def __str__(self) -> str:
        assert self.path is not None
        return os.fspath(self.path)

    def __fspath__(self) -> str:
        return str(self)


@dataclass
class Flag:
    """Describes a flag object that can be used when executing objects.

    Parameters
    ----------
    flag: The flag to use when executing the objects. Examples of flags include:
      'cores=8', 'flags=s', 'help', 'version' etc. Check the SAGA GIS
      documentation if you want to find out more about flags.
    """

    flag: Optional[str] = field(default=None)

    def __str__(self) -> str:
        if self.flag is None:
            return ''
        if isinstance(self.flag, str) and not self.flag.startswith('--'):
            return ''.join(['--' + self.flag])
        return self.flag

    def __bool__(self) -> bool:
        return self.flag is not None

    def __eq__(self, other) -> bool:
        return str(self) == other


# TODO: Switch inheritance from dict to UserDict
# read Fluent Python pg 490-493 for details


@dataclass
class Parameters(dict[str, str]):
    """The SAGA GIS tool parameters.

    This object inherits from 'dict'.

    Parameters
    ----------
    **kwargs: The tool parameters as keyword arguments. For example,
      'elevation=/path/to/raster' could be a keyword argument.

    Attributes
    ----------
    formatted: A tuple of the parameters formatted as required by SAGA GIS.

    Examples
    ---------
    >>> params = Parameters(elevation='path/to/raster',
    ...                     grid='path/to/grid',
    ...                     method=0)
    >>> print(params)
    -ELEVATION=path/to/raster -GRID=path/to/grid -METHOD=0
    """

    def __init__(self, **kwargs: SupportsStr) -> None:
        for param, value in kwargs.items():
            kwargs[param] = str(value)
        super().__init__(**kwargs)

    def __str__(self) -> str:
        return ' '.join(self.formatted)

    def __repr__(self) -> str:
        return dict.__repr__(self)

    def __getattr__(self, name: str) -> str:
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e) from e

    def __setattr__(self, name, value) -> None:
        self[name] = value

    @property
    def formatted(self) -> list[str]:
        return self._format_parameters(self)

    @staticmethod
    def _format_parameters(parameters: Parameters) -> list[str]:
        """Used to format the parameters as required by SAGAGIS."""
        params = []
        param_format = '-{PARAM}={value}'
        for param, value in parameters.items():
            params.append(param_format.format(PARAM=param.upper(), value=value))
        return params


@dataclass
class Executable(ABC):
    """Describes an object that is executable."""

    @abstractmethod
    def execute(self) -> Union[ToolOutput, Iterable[ToolOutput], Output]:
        """Implements the execution behaviour of the object."""


@dataclass
class SagaExecutable(Executable):
    """Describes an executable inside SAGAGIS."""

    @property
    @abstractmethod
    def command(self):
        """Gets the current command."""

    @property
    def flag(self):
        """Gets the current flag."""
        return self._flag

    @flag.setter
    def flag(self, flag: Union[SupportsStr, None]):
        """Sets the current flag."""
        if flag is not None:
            flag = str(flag)
        self._flag = Flag(flag)

    @flag.deleter
    def flag(self):
        """Deletes the current flag."""
        self._flag = Flag()


@dataclass
class SAGA(SagaExecutable):
    """The SAGA GIS main program as an object.

    This object inherits from 'SagaExecutable'.

    Parameters
    ----------
    saga_cmd: The file path to the 'saga_cmd' file or a SAGACMD object.
    For information on where to find it, check the following link:
      https://sourceforge.net/projects/saga-gis/files/SAGA%20-%20Documentation/Tutorials/Command_Line_Scripting/.

    Attributes
    ----------
    saga_cmd: A 'SAGACMD' object describing the 'saga_cmd' executable.
    flag: A 'Flag' object describing the flag that will be used when
      running the command.
    command: The command that will be executed with the 'execute' method.
    temp_dir: A temporary directory where temporary files will be saved to.
    temp_files: A list of temporary files.

    Methods
    -------
    get_library: Takes as input a SAGA GIS library name (e.g 'ta_morphometry')
      and returns a 'Library' object.
    get_tool: Takes as input a library tool name (e.g '0')
      and returns a 'Tool' object.
    execute: Executes the command. To see the command that will be
      executed, check the 'command' property of this class.
    temp_dir_cleanup: Deletes the temporary directory.
    """

    saga_cmd: Optional[Union[PathLike, SAGACMD]] = field(default=None)

    def __post_init__(self) -> None:
        if not isinstance(self.saga_cmd, SAGACMD):
            self.saga_cmd = SAGACMD(self.saga_cmd)
        self._flag = Flag()
        self._temp_dir = temp_dir()

    def __truediv__(self, library: Union[Library, SupportsStr]):
        if not isinstance(library, Library):
            return self.get_library(library=str(library))
        return library

    @property
    def temp_dir(self) -> Path:
        if not self._temp_dir.exists():
            self._temp_dir = temp_dir()
        return self._temp_dir

    @property
    def temp_files(self):
        """Lists the temporary files.

        The temporary files are named by their parameter
        name and unix time, separated by an underscore.
        """
        return list(self.temp_dir.iterdir())

    def temp_dir_cleanup(self):
        """Removes the temporary directory."""
        files = self.temp_files[:]
        shutil.rmtree(self.temp_dir)
        print('The following files were removed:')
        for file in files:
            assert not file.exists()
            print(file)

    @property
    def command(self) -> Command:
        assert isinstance(self.saga_cmd, SupportsStr)
        return Command(self.saga_cmd, self.flag)

    def get_library(self, library: str) -> Library:
        """Get a SAGA GIS Library object.

        Args:
            library: The library name. For example, 'ta_morphometry'.
              Check the SAGA GIS documentation for more details:
              https://saga-gis.sourceforge.io/saga_tool_doc/9.3.1/index.html

        Returns:
            Library: An object describing the SAGA GIS library.
        """
        return Library(saga=self, library=library)

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
        return Tool(library=library_, tool=tool)

    def execute(self) -> Output:
        return Output(self.command.execute())


@dataclass
class Library(SagaExecutable):
    """Describes a SAGA GIS library.

    Parameters
    ----------
    saga: A 'SAGA' object.
    library: The SAGA GIS library name.

    Attributes
    ----------
    saga: The 'SAGA' object used to access this library.
    flag: A 'Flag' object describing the flag that will be used when
      executing the command.
    command: The command that will be executed with the 'execute' method.
    library: The name of the library.

    Methods
    -------
    get_tool: Takes as input a tool name inside the library (e.g. '0')
      and returns a 'Tool' object.
    execute: Executes the command. To see the command that will be
      executed, check the 'command' property of this class.
    """

    saga: SAGA
    library: str

    def __post_init__(self) -> None:
        self._flag = self.saga.flag

    def __str__(self):
        return self.library

    def __truediv__(self, tool: Union[Tool, SupportsStr]):
        if not isinstance(tool, Tool):
            return self.get_tool(tool=str(tool))
        return tool

    @property
    def command(self) -> Command:
        assert isinstance(self.saga.saga_cmd, SupportsStr)
        return Command(self.saga.saga_cmd, self.flag, self.library)

    def get_tool(self, tool: str) -> Tool:
        """Get a SAGA GIS Tool object.

        Args:
            tool: The name for the tool inside the library. For more
              details, check the SAGA GIS documentation:
              https://saga-gis.sourceforge.io/saga_tool_doc/9.3.1/index.html

        Returns:
            Tool: An object describing the SAGA GIS tool.
        """
        return Tool(library=self, tool=tool)

    def execute(self) -> Output:
        return Output(self.command.execute())


TTool = TypeVar("TTool", bound='Tool')


@dataclass
class Tool(SagaExecutable):
    """Describes a SAGA GIS tool.

    Parameters
    ----------
    library: The SAGA GIS library object.
    tool: The tool name.

    Attributes
    ----------
    saga_cmd: A 'SAGACMD' object describing the 'saga_cmd' executable.
    flag: A 'Flag' object describing the flag that will be used when
      executing the command.
    command: The command that will be executed with the 'execute' method.
    library: The SAGA GIS library object.
    tool: The tool name.
    parameters: A 'Parameters' object describing the parameters of the tool.

    Methods
    -------
    execute: Takes as input keyword arguments which will be
      used to construct a 'Parameters' object and execute the tool.
      Example of a keyword argument would be 'elevation=/path/to/raster.
      To see the command that will be executed, check the 'command'
      attribute of this class.
    """

    library: Library
    tool: str
    parameters: Parameters = field(default_factory=Parameters)

    def __post_init__(self) -> None:
        self._flag = self.library.flag
        self.parameters = Parameters()

    def __str__(self):
        return self.tool

    def __call__(self: TTool, **kwargs: SupportsStr) -> TTool:
        """Uses keyword argument to define the tool parameters."""
        if self.parameters:
            self._del_attr_params()
        self.parameters = Parameters(**kwargs)
        self._set_attr_params()
        return self

    def _del_attr_params(self):
        """Delets the attributes describing parameters."""
        for param in self.parameters:
            # Delete all previous parameter attributes.
            delattr(self, param)

    def _set_attr_params(self):
        """Sets the parameters of the tool as attributes.

        Besides setting attributes, it also replaces 'temp'
        values with a temporary file location.
        """
        for param, value in self.parameters.items():
            value = str(value)
            val_as_path = Path(value)
            if val_as_path.stem == 'temp':
                suffix = val_as_path.suffix
                unix = str(time.time()).split('.', maxsplit=1)[0]
                self.parameters[param] = str(
                    self.library.saga.temp_dir / f'{param}_{unix}{suffix}'
                )
            setattr(self, param, self.parameters[param])

    def __getattr__(self, name: str) -> Any:
        pass

    @property
    def command(self) -> Command:
        assert isinstance(self.library.saga.saga_cmd, SupportsStr)
        return (
            Command(self.library.saga.saga_cmd,
                    self.flag,
                    self.library,
                    self.tool,
                    *self.parameters.formatted)
        )

    def __or__(self, tool: Tool) -> Pipeline:
        return Pipeline(self) | (tool)

    def execute(
        self,
        verbose: bool = False,
        **kwargs: SupportsStr
    ) -> ToolOutput:
        if kwargs:
            self(**kwargs)
        for param, value in self.parameters.items():
            value_as_path = Path(value)
            if value_as_path.parent.exists() and not value_as_path.suffix:
                value = str(infer_file_extension(value_as_path))
                self.parameters[param] = value
        completed_process = self.command.execute(verbose=verbose)
        return ToolOutput(completed_process, self.parameters)


TPipeline = TypeVar("TPipeline", bound='Pipeline')


@dataclass
class Pipeline(Executable):
    """Used to chain tools.

    In order to create a 'Pipeline' object, you must use the 'or'
    operator between two 'Tool' objects or between a 'Pipeline' object and a
    'Tool' object.

    Parameters
    ----------
    tool: The tool object which will initialize the 'Pipeline' object.
      This corresponds to the first tool that will be ran.

    Attributes
    ----------
    tools: A list of the tools in the pipeline.

    Methods
    ----------
    execute: Used to execute each tool, one after the other.

    Examples
    ---------
    >>> dem = 'path/to/raster.tif'
    >>> dem_preprocessed = 'path/to/output_raster.tif'
    >>> saga = SAGA('path/to/saga_cmd')
    >>> preprocessor = saga / 'ta_preprocessor'
    >>> route_detection = preprocessor / 'Sink Drainage Route Detection'
    >>> sink_removal = preprocessor / 'Sink Removal'
    >>> pipe = (
    >>>    route_detection(elevation=dem, sinkroute='temp.sdat') |
    >>>    sink_removal(dem=route_detection.elevation,
    >>>                 route_detection.sinkroute,
    >>>                 dem_preproc=dem_preprocessed)
    >>> )
    >>> outputs = pipe.execute(verbose=True)
    """

    tools: list[Tool]

    def __init__(
        self,
        tool: Tool
    ):
        self.tools = [tool]

    def __or__(self: TPipeline, tool: Tool) -> TPipeline:
        self.tools.append(tool)
        return self

    def execute(self, verbose: bool = False) -> list[ToolOutput]:
        """Executes the tools in the pipeline.

        Args:
            verbose: Wether or not to print the output text after
              the execution of each tool.
        """
        outputs = []
        for tool in self.tools:
            print(self._format_tool_string(tool))
            output = tool.execute(verbose=verbose)
            outputs.append(output)
        return outputs

    @staticmethod
    def _format_tool_string(tool: Tool):
        string = []
        string.extend(['-'*25, '\n'])
        string.extend([str(tool.library), ' ', str(tool), '\n'])
        string.extend(['    ', str(tool.parameters), '\n'])
        return ''.join(str(element) for element in string)

    def __str__(self):
        string = [self._format_tool_string(tool) for tool in self.tools]
        return ''.join(str(element) for element in string)


class PipelineError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


@dataclass
class Command:
    """The commands to be executed.

    Attributes
    ----------
    args: The args to be passed to the 'subprocess.Popen' function.

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

    def execute(self, verbose: bool = False) -> subprocess.Popen:
        """Executes the process.

        Args:
            verbose: This bool should be True only when the args
              correspond to a tool.
        """
        process = subprocess.Popen(self.args, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        if verbose:
            dynamic_print(process)
        return process


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

    completed_process: subprocess.Popen
    text: Union[str, None] = field(init=False, default=None)

    def __post_init__(self) -> None:
        if self.completed_process.stdout is not None:
            self.text = self.completed_process.stdout.read()


@dataclass
class ToolOutput(Output):
    parameters: Parameters = field(default_factory=Parameters)

    def get_raster(
        self,
        parameters: Union[Sequence[str], str]
    ) -> list[Raster]:

        from .objects import Raster

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

        from .objects import Vector

        if isinstance(parameters, str):
            parameters = [parameters]
        return (
            [Vector(v) for k, v in self.parameters.items()
             if k in parameters]
        )
