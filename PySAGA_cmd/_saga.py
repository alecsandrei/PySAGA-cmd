import subprocess
from typing import Type
from attrs import define, field

from PySAGA_cmd._output import Output


@define
class SAGA:
    """This class represents a SAGA GIS environment.

    Parameters
    ----------
    saga_cmd : str
        The location of the 'saga_cmd' file.

    Attributes
    ----------
    saga_cmd : str
        The location of the 'saga_cmd' file.
    command : list
        The current command pipe, e.g. ['saga_cmd', 'ta_morphometry', '0'].
    flag : str, default=None
        The current flag inside the command pipe e.g. 'help' or 'version'.

    Examples
    --------
        >>> from PySAGA_cmd import SAGA
        
        Constructing a SAGA class.
        >>> saga_env = SAGA('/usr/local/bin/saga_cmd') # on a Linux operating system
        >>> saga_env = SAGA('C:\Program Files\SAGA\saga_cmd') # on a Windows operating system

        Using a flag and removing it afterwards.
        >>> saga_env.flag = 'help'
        >>> print(saga_env.run_command().text)
        >>> saga_env.remove_flag()

        Constructing a Library class.
        >>> saga_library = saga_env.get_library(library_name='ta_morphometry')

        Constructing a Tool class.
        >>> saga_tool = saga_library.get_tool('0') # Option 1
        >>> saga_tool = saga_env.get_tool(library_name='ta_morphometry', tool_name='0') # Option 2

        Executing a tool.
        >>> output = saga_tool.run_command(elevation='elevation.tif',
                                           slope='slope.tif',
                                           aspect='slope.tif')
        Get the text output.        
        >>> print(output.text)
    """

    saga_cmd: str
    command: list[str] = field(init=False)
    _flag: None = field(default=None, init=False)

    def __attrs_post_init__(self):
        self.command = [self.saga_cmd]

    def get_flag(self) -> str:
        """This getter will return the current flag in the command pipe."""
        return self._flag
    
    def set_flag(self, flag) -> None:
        """This setter adds a flag to the current command pipe, replacing the previous one.
        Args:
            flag: Possible flags are: 'help', 'version', 'batch', 'docs', 'cores'.
        """
        if flag is None and self._flag is not None:
            self.remove_flag()
        elif flag is None:
            pass
        elif self._flag is None:
            self.command.insert(1, f'--{flag}')
        else:
            self.command[1] = f'--{flag}'
        self._flag = flag
    
    def remove_flag(self):
        """This method sets the flag to None and deletes it from the command pipe."""
        if self._flag is None:
            raise ValueError('There is no flag in the command pipe.')
        del self.command[1]
        self._flag = None

    flag = property(get_flag, set_flag, remove_flag)

    def get_library(self, library_name: str) -> Type['Library']:
        """This method creates a Library class instance.
        Args:
            library: The name for a library (e.g. ta_morphometry).

        Returns:
            Library: A Library class instance.
        """
        library = Library(self, library_name)
        return library
    
    def get_tool(self, library: str, tool: str) -> Type['Tool']:
        """This method creates a Tool class instance.
        Args:
            library: The name for a library (e.g. ta_morphometry).
            tool: The name (index) of a tool inside the library (e.g. '17') that is shown inside square brackets
                when printing the Library object.

        Returns:
            Tool: A Tool class instance.
        """
        library = self.get_library(library)
        return library.get_tool(tool)
    
    def run_command(self, *args, **kwargs) -> Output:
        """This method executes a command with optinal arguments and keyword arguments.
        Args:
            *args: Additional command-line arguments.
            **kwargs: Additional command-line options specified as key-value pairs.

        Returns:
            str: The standard output of the executed command.
        """
        if args:
            for arg in args:
                self.command.append(arg)
        if kwargs:
            for k, v in kwargs.items():
                self.command.append(f'-{k.upper()}')
                self.command.append(v)
        result = subprocess.run(self.command, capture_output=True, text=True)
        output = Output(result, kwargs)
        return output


@define(init=False)
class Library(SAGA):
    """This class represents a SAGA GIS library. It inherits from the SAGA class.

    Parameters
    ----------
    saga : SAGA
        SAGA class instance.
    library_name : str
        The name of the SAGA GIS library.
            For more information execute the 'run_command' method of a SAGA object and get
            the 'text' attribute of the output object. For example:
            >>> saga_env = SAGA(saga_cmd='saga_cmd')
            >>> print(saga_env.run_command().text)

    Attributes
    ----------
    library_name : str
        The name of the SAGA GIS library.
    command : list
        The current command pipe, e.g. ['saga_cmd', 'ta_morphometry', '0'].
    saga : SAGA
        The SAGA class instance.
    flag : str, default=None
        The current flag inside the command pipe e.g. 'help' or 'version'.

    Examples
    --------
    >>> from PySAGA_cmd import SAGA, Library

    Constructing a Library class.
        Option 1
    >>> saga_env = SAGA('/usr/local/bin/saga_cmd')  # on a Linux operating system
    >>> saga_library = saga_env.get_library('ta_morphometry')
        Option 2
    >>> saga_env = SAGA('/usr/local/bin/saga_cmd')  # on a Linux operating system
    >>> saga_library = Library(saga_env, 'ta_morphometry')
    """

    saga: SAGA
    library_name: str

    def __init__(self, saga: SAGA, library_name: str):
        self.saga = saga
        self.library_name = library_name
        super().__init__(self.saga.saga_cmd)
        self.command.append(self.library_name)
        self.set_flag(self.saga.get_flag())
        

    def get_tool(self, tool_name: str) -> Type['Tool']:
        """This method creates a Tool class instance.
        Args:
            tool_name: The name of a tool inside the library (e.g. '17').

        Returns:
            Tool: A Tool class instance.
        """
        tool = Tool(self.saga, self.library_name, tool_name)
        return tool


@define(init=False)
class Tool(Library):
    """This class represents a SAGA GIS tool. It inherits from the Library class.

    Parameters
    ----------
    saga : SAGA
        SAGA class instance.
    library_name : Library
        The name of the library the tool resides in.
    tool_name : str
        The name of a tool inside the library (e.g. '17') that is shown inside square brackets.
            For more information execute the 'run_command' method of a Library object and get
            the 'text' attribute of the output object. For example:
            >>> saga_env = SAGA(saga_cmd='saga_cmd')
            >>> saga_library = saga_env.get_library('ta_morphometry')
            >>> print(saga_library.run_command().text)

    Attributes
    ----------
    saga : SAGA
        SAGA class instance.
    library_name : Library
        The name of the library the tool resides in.
    tool_name : str
        The name of a tool inside the library (e.g. '17') that is shown inside square brackets.
            For more information execute the 'run_command' method of a Library object and get
            the 'text' attribute of the output object. For example:
            >>> saga_env = SAGA(saga_cmd='saga_cmd')
            >>> saga_library = saga_env.get_library('ta_morphometry')
            >>> print(saga_library.run_command().text)
    tool : str
        The index of the SAGA tool inside the library.
    flag : str, default=None
        The current flag inside the command pipe e.g. 'help' or 'version'.

    Examples
    --------
    >>> from PySAGA_cmd import SAGA, Library, Tool

    Constructing a Tool class.
        Option 1
    >>> saga_env = SAGA('/usr/local/bin/saga_cmd')  # on a Linux operating system
    >>> saga_library = saga_env.get_library('ta_morphometry')
    >>> saga_tool = saga_library.get_tool(tool='0')
        Option 2
    >>> saga_env = SAGA('/usr/local/bin/saga_cmd')  # on a Linux operating system
    >>> saga_library = Library(saga_env, 'ta_morphometry')
    >>> saga_tool = Tool(saga_library, '0')
        Option 3
    >>> saga_env = SAGA('/usr/local/bin/saga_cmd')  # on a Linux operating system
    >>> saga_tool = saga_env.get_tool(library_name='ta_morphometry', tool_name='0')
    """

    saga: SAGA
    library_name: str
    tool_name: str

    def __init__(self, saga: SAGA, library_name: str, tool_name: str):
        self.saga = saga
        self.library_name = library_name
        self.tool_name = tool_name
        super().__init__(self.saga, self.library_name)
        self.command.append(self.tool_name)
        self.set_flag(self.saga.get_flag())


if __name__ == '__main__':
    dem = 'DEM.tif'
    shade = 'shade.tif'
    saga_env = SAGA('saga_cmd')
    saga_tool = saga_library.get_tool('0')
    saga_tool = saga_env.get_tool('ta_lighting', '0')
    output = saga_tool.run_command(elevation=dem,
                                   shade=shade,
                                   method='2')
    output.plot_raster('elevation')
