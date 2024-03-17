"""Contains the main functionalities of the PySAGA-cmd package."""

from __future__ import annotations

import os
import shutil
import tempfile
import concurrent.futures
import time
from typing import (
    Union,
    Optional,
    Protocol,
    Iterable,
    TypeVar,
    Any,
    runtime_checkable,
    Literal,
)
from pathlib import Path
import subprocess
from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import (
    dataclass,
    field
)
from functools import partial
import csv
import re
from collections import (
    UserDict,
    abc
)

from PySAGA_cmd.utils import (
    check_is_executable,
    search_saga_cmd,
    infer_file_extension,
    dynamic_print,
)
from PySAGA_cmd.objects import (
    Raster,
    Vector
)


def temp_dir():
    return Path(tempfile.mkdtemp())


@runtime_checkable
class SupportsStr(Protocol):
    def __str__(self) -> str:
        ...


PathLike = Union[str, os.PathLike]


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
    SubprocessError: If 'path' can not be executed.
    OSError: If 'path' can not be executed.
    """

    path: Optional[PathLike] = field(default=None)

    def __post_init__(self) -> None:
        if self.path is None:
            print(
                'Path to "saga_cmd" was not provided.',
                'Attempting to find it.'
            )
            self.path = search_saga_cmd()
            print(f'saga_cmd found at "{self.path}".')
        elif not isinstance(self.path, Path):
            self.path = Path(self.path)
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
            return ''.join(['--', self.flag])
        return self.flag

    def __bool__(self) -> bool:
        return self.flag is not None

    def __eq__(self, other) -> bool:
        return str(self) == other


class Parameters(UserDict[str, str]):
    """The SAGA GIS tool parameters.

    This object inherits from 'dict'.

    Parameters
    ----------
    tool: The SAGA Tool to which the parameters correspond.
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

    def __init__(self, tool: Tool, **kwargs: SupportsStr) -> None:
        self.tool = tool
        super().__init__()
        # Converts parameter values to str.
        for param, value in kwargs.items():
            self[param] = value

    def __setitem__(self, param: str, value: SupportsStr) -> None:
        """Always converts value to string.

        It also replaces 'temp' named files with a temporary unique path.
        """
        value = str(value)
        path = Path(value)
        exists = path.exists()
        suffix = path.suffix
        if path.stem == 'temp' and not exists:
            unix = str(time.time()).split('.', maxsplit=1)[0]
            value = str(
                self.tool.library.saga.temp_dir / f'{param}_{unix}{suffix}'
            )
        elif exists and not suffix:
            suffix = infer_file_extension(path).suffix
            value = str(path.with_suffix(suffix))
        return super().__setitem__(param, value)

    def __str__(self) -> str:
        return ' '.join(self.formatted)

    @property
    def formatted(self) -> list[str]:
        return (
            [f'-{param.upper()}={value}' for param, value in self.items()]
        )


class Executable(ABC):
    """Describes an object that is executable."""

    @abstractmethod
    def execute(self) -> Union[ToolOutput, Iterable[ToolOutput], Output]:
        """Implements the execution behaviour of the object."""


class SAGAExecutable(Executable):
    """Describes an executable inside SAGAGIS."""

    @abstractmethod
    def __str__(self):
        """The name of the object."""

    @property
    @abstractmethod
    def command(self):
        """Gets the current command."""

    @property
    def flag(self):
        """Gets the current flag."""
        return self._flag

    @flag.setter
    def flag(self, flag: Optional[SupportsStr]):
        """Sets the current flag."""
        if flag is not None:
            flag = str(flag)
        self._flag = Flag(flag)

    @flag.deleter
    def flag(self):
        """Deletes the current flag."""
        self._flag = Flag()


MajMinPatch = tuple[int, int, int]


@dataclass
class SAGA(SAGAExecutable):
    """The SAGA GIS main program as an object.

    This object inherits from 'SAGAExecutable'.

    Parameters
    ----------
    saga_cmd: The file path to the 'saga_cmd' file or a SAGACMD object.
    For information on where to find it, check the following link:
      https://sourceforge.net/projects/saga-gis/files/SAGA%20-%20Documentation/Tutorials/Command_Line_Scripting/.
    version: The version of SAGA GIS.

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
    get_raster_formats: Get the raster extensions allowed by GDAL.
    get_vector_formats: Get the vector extensions allowed by GDAL.
    """

    saga_cmd: Optional[Union[PathLike, SAGACMD]] = field(default=None)
    version: Optional[MajMinPatch] = field(default=None)
    _raster_formats: Optional[set[str]] = field(
        init=False, default=None, repr=False
    )
    _vector_formats: Optional[set[str]] = field(
        init=False, default=None, repr=False
    )

    def __post_init__(self) -> None:
        if not isinstance(self.saga_cmd, SAGACMD):
            self.saga_cmd = SAGACMD(self.saga_cmd)
        self._flag = Flag()
        self._temp_dir = temp_dir()
        if self.version is None:
            self.version = get_saga_version(self)

    def __truediv__(self, library: Union[Library, SupportsStr]):
        if not isinstance(library, Library):
            return self.get_library(library=str(library))
        return library

    def __str__(self):
        return str(self.saga_cmd)

    def get_raster_formats(self):
        if self._raster_formats is None:
            formats = get_formats(self, type_='raster')
            if formats is None:
                formats = set()
            # '.sdat', '.sgrd', '.sg-grd-z' are not included in the output
            # of 'GDAL Formats'.
            self._raster_formats = formats.union(
                ['sdat', 'sgrd', 'sg-grd-z']
            )
        return self._raster_formats

    def get_vector_formats(self):
        if self._vector_formats is None:
            self._vector_formats = get_formats(self, type_='vector')
        return self._vector_formats

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

    def execute(self, ignore_stderr: bool = True) -> Output:
        """Executes the command.

        Args:
            ignore_stderr: Whether or not the presence of a
              stderr raises an error.

        Returns:
            Output: An object describing the output of the execution.
        """
        return Output(self, self.command.execute(), ignore_stderr)


@dataclass
class Library(SAGAExecutable):
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

    def execute(self, ignore_stderr: bool = True) -> Output:
        """Executes the command.

        Args:
            ignore_stderr: Whether or not the presence of a
              stderr raises an error.

        Returns:
            Output: An object describing the output of the execution.
        """
        return Output(self, self.command.execute(), ignore_stderr)


TTool = TypeVar("TTool", bound='Tool')


@dataclass
class Tool(SAGAExecutable):
    """Describes a SAGA GIS tool.

    Parameters
    ----------
    library: The SAGA GIS library object.
    tool: The tool name.

    Attributes
    ----------
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
    parameters: Parameters = field(init=False)

    def __post_init__(self) -> None:
        self._flag = self.library.flag
        self.parameters = Parameters(self)

    def __str__(self):
        return self.tool

    def __call__(self: TTool, **kwargs: SupportsStr) -> TTool:
        """Uses keyword argument to define the tool parameters."""
        if self.parameters:
            self._del_attr_params()
        self.parameters = Parameters(self, **kwargs)
        self._set_attr_params()
        return self

    def _del_attr_params(self):
        """Delets the attributes describing parameters."""
        for param in self.parameters:
            # Delete all previous parameter attributes.
            delattr(self, param)

    def _set_attr_params(self):
        """Sets the parameters of the tool as attributes."""
        for param, value in self.parameters.items():
            setattr(self, param, value)

    def __getattr__(self, name: str) -> Any:
        pass

    @property
    def command(self) -> Command:
        assert isinstance(self.library.saga.saga_cmd, SupportsStr)
        return (
            Command(
                self.library.saga.saga_cmd,
                self.flag,
                self.library,
                self.tool,
                *self.parameters.formatted
            )
        )

    def __or__(self, tool: Tool) -> Pipeline:
        return Pipeline(self) | (tool)

    def get_verbose_message(self) -> str:
        string = []
        string.extend(['-'*25, '\n'])
        string.extend([str(self.library), ' / ', str(self), '\n'])
        string.extend(['    ', str(self.parameters), '\n'])
        return ''.join(str(element) for element in string)

    def execute(
        self,
        verbose: bool = False,
        ignore_stderr: bool = False,
        infer_obj_type: bool = True,
        **kwargs: SupportsStr
    ) -> ToolOutput:
        """Execute the command.

        Args:
            verbose: Whether or not to print the progress of each tool
              when it's executing.
            ignore_stderr: Whether or not the presence of a stderr
              raises an error.
            infer_obj_type: Whether or not to infer the output as
              either Vector or Raster objects.

        Returns:
            Output: An object describing the output of the execution.
        """
        if kwargs:
            self(**kwargs)

        if verbose:
            print(self.get_verbose_message())

        command_partial = partial(self.command.execute, verbose)
        saga = self.library.saga
        if (
            not any((saga._raster_formats, saga._vector_formats))
            and infer_obj_type
        ):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                funcs = (
                    saga.get_raster_formats,
                    saga.get_vector_formats,
                    command_partial
                )
                output = list(executor.map(lambda f: f(), funcs))[-1]

        else:
            output = command_partial()
        return ToolOutput(self, output, ignore_stderr)


TPipeline = TypeVar("TPipeline", bound='Pipeline')


@dataclass
class Pipeline(Executable, abc.Sequence):
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
    ) -> None:
        self.tools = [tool]

    def __len__(self) -> int:
        return len(self.tools)

    def __getitem__(self, idx) -> Any:
        return self.tools[idx]

    def __or__(self: TPipeline, tool: Tool) -> TPipeline:
        self.tools.append(tool)
        return self

    def execute(
        self,
        verbose: bool = False,
        ignore_stderr: bool = False
    ) -> list[ToolOutput]:
        """Executes the tools in the pipeline.

        Args:
            verbose: Wether or not to print the output text after
              the execution of each tool.
        """
        outputs = []
        for tool in self.tools:
            output = tool.execute(verbose=verbose, ignore_stderr=ignore_stderr)
            outputs.append(output)
        return outputs

    def __str__(self) -> str:
        string = [tool.get_verbose_message() for tool in self.tools]
        return ''.join(str(element) for element in string)


class PipelineError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


@dataclass
class Command(abc.Sequence):
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

    def __len__(self):
        return len(self.args)

    def __getitem__(self, idx) -> Any:
        return self.args[idx]

    def __str__(self) -> str:
        return ' '.join(f'"{arg}"' for arg in self.args)

    def execute(self, verbose: bool = False) -> subprocess.Popen:
        """Executes the process.

        Args:
            verbose: This bool should be True only when the args
              correspond to a tool.
        """
        process = subprocess.Popen(
            self.args,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if verbose:
            dynamic_print(process)
        return process


@dataclass
class Output:
    """The output of the child process.

    Parameters
    ----------
    saga_executable: A SAGA, Library or Tool object.
    completed_process: A 'CompletedProcess' object that was returned by
      a command execution.
    ignore_stderr: Whether or not the presence of a stderr raises an error.

    Attributes
    ----------
    stdout: The 'stdout' attribute of the 'CompletedProcess' object as string.
    stderr: The 'stderr' attribute of the 'CompletedProcess' object as string.
    stdin: The 'stdin' attribute of the 'CompletedProcess' object as string.
    """

    saga_executable: Union[SAGA, Library, Tool]
    completed_process: subprocess.Popen
    ignore_stderr: bool
    stdout: Optional[str] = field(init=False, default=None)
    stderr: Optional[str] = field(init=False, default=None)
    stdin: Optional[str] = field(init=False, default=None)

    def __post_init__(self) -> None:
        if self.completed_process.stdout is not None:
            self.stdout = self.completed_process.stdout.read()
        if (
            (stderr := self.completed_process.stderr) is not None
            and (read := stderr.read().strip())
        ):
            if not self.ignore_stderr:
                raise ExecutionError(read, self.saga_executable)
            self.stderr = read
        if self.completed_process.stdin is not None:
            self.stdin = self.completed_process.stdin.read()


Files = dict[str, Union[Path, Raster, Vector]]


@dataclass
class ToolOutput(Output):
    """Describes the output of the execution of a Tool.

    Parameters
    ----------
    saga_executable: A Tool object.
    completed_process: A 'CompletedProcess' object that was returned by
      a command execution.
    ignore_stderr: Whether or not the presence of a stderr raises an error.

    Attributes
    ----------
    stdout: The 'stdout' attribute of the 'CompletedProcess' object as string.
    stderr: The 'stderr' attribute of the 'CompletedProcess' object as string.
    stdin: The 'stdin' attribute of the 'CompletedProcess' object as string.
    rasters: The outputs identified as rasters (according to
      their file extension).
    vectors: The outputs identified as vectors (according to
      their file extension).
    files: All of the output files.
    """

    saga_executable: Tool
    _outputs: Optional[Files] = field(init=False, default=None)

    # TODO: add support for output tables aswell.

    @property
    def rasters(self) -> dict[str, Raster]:
        def filtering_func(pair) -> bool:
            return isinstance(pair[1], Raster)
        filtered = filter(filtering_func, self.files.items())
        return dict(filtered)  # type: ignore

    def is_raster(self, path: Path) -> bool:
        formats = self.saga_executable.library.saga._raster_formats
        assert path.exists()
        if formats is not None and path.suffix.strip('.') in formats:
            return True
        return False

    @property
    def vectors(self) -> dict[str, Vector]:
        def filtering_func(pair) -> bool:
            return isinstance(pair[1], Vector)
        filtered = filter(filtering_func, self.files.items())
        return dict(filtered)  # type: ignore

    def is_vector(self, path: Path) -> bool:
        formats = self.saga_executable.library.saga._vector_formats
        assert path.exists()
        if formats is not None and path.suffix.strip('.') in formats:
            return True
        return False

    @property
    def files(self) -> Files:
        if self._outputs is None:
            self._outputs = self.get_files()
        return self._outputs

    def get_files(self) -> Files:
        outputs: Files = {}
        for param, value in self.saga_executable.parameters.items():
            try:
                path = Path(value)
            except Exception:
                continue
            else:
                if not path.is_file():
                    continue
                if self.is_raster(path):
                    outputs[param] = Raster(path)
                elif self.is_vector(path):
                    outputs[param] = Vector(path)
                else:
                    outputs[param] = path
        return outputs


def get_saga_version(saga: SAGA) -> Optional[MajMinPatch]:
    """Get's the SAGA version using the version flag."""
    saga.flag = 'version'
    stdout = saga.execute().stdout
    del saga.flag
    assert stdout is not None
    pattern = r'\d+\.\d+\.\d+'
    match = re.search(pattern, stdout)
    if match:
        maj, min_, patch = tuple(map(int, match.group(0).split('.')))
        return (maj, min_, patch)
    else:
        print(
            f'Could not parse SAGA version from stdout {stdout}.',
            'To make use of all the functionality of the package,',
            'Instantiate the "SAGA" object with a version parameter.'
        )
        return None


def get_formats(
        saga: SAGA,
        type_: Literal['raster', 'vector']
) -> Optional[set[str]]:
    """Get's the possible raster or vector file extensions.

    Requires SAGA >= 4.0.0.
    """
    if saga.version is None or saga.version[0] < 4:
        return None
    gdal_formats = saga / 'io_gdal' / 10

    # Create an empty temporary file.
    with tempfile.NamedTemporaryFile() as tmp:
        path = Path(tmp.name)

        gdal_formats_execute = partial(
            gdal_formats.execute,
            formats=path,
            acces=2,
            recognized=1,
            verbose=False,
            infer_obj_type=False,
        )
        assert type_ in ['raster', 'vector']

        if type_ == 'raster':
            gdal_formats_execute(type='0')
        else:
            gdal_formats_execute(type='1')

        reader = csv.reader(
            [string.decode('utf-8') for string in tmp.readlines()],
            dialect="excel-tab"
        )
        last_row = tuple(reader)[-1]
        third_column = last_row[2]
        extensions = re.findall(r'\.(\w+)', third_column)
    return set(extensions)


class ExecutionError(Exception):
    """Raised when an execution outputs a stderr."""
    def __init__(self, stderr: str, saga_executable: SAGAExecutable):
        self.stderr = stderr
        super().__init__(
            'A stderr was detected after the execution of '
            f'"{saga_executable}": \n'
            f'{self.stderr}\n'
            'If you want to suppress this error, set "ignore_stderr" '
            'to True when executing.'
        )
