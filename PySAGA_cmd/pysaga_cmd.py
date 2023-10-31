"""
A module that allows you to easly run SAGA GIS tools in a Python environment.
"""

# Author: Cuvuliuc Alex-Andrei <cuvuliucalexandrei@gmail.com>

import subprocess

from typing import Type, Union


class SAGA:
    """
    Parameters
    ----------
    command : str or list
        The location of the 'saga_cmd' file.

    Attributes
    ----------
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
        >>> print(saga_env.run_command())
        >>> saga_env.remove_flag()

        Constructing a Library class.
        >>> saga_library = saga_env.get_library('ta_morphometry')

        Constructing a Tool class.
        >>> saga_tool = saga_library.get_tool('0') # Option 1
        >>> saga_tool = saga_env.get_tool(library='ta_morphometry', tool='0') # Option 2

        Executing a tool.
        >>> output = saga_tool.run_command(elevation='elevation.tif',
                                           slope='slope.tif',
                                           aspect='slope.tif')
    """

    def __init__(self, command: Union[str, list]):
        self.command = command
        if isinstance(self.command, str):
            self.command = [self.command]
        self._flag = None

    def __str__(self):
        return self.run_command()

    def __repr__(self):
        return self.run_command()

    @property
    def flag(self):
        """This property stores the current flag in the command pipe."""
        return self._flag
    
    @flag.setter
    def flag(self, flag):
        """This setter adds a flag to the current command pipe, replacing the previous one.
        Args:
            flag: Possible flags are: 'help', 'version', 'batch', 'docs', 'cores'.

        Returns:
            str: command output
        """
        if self._flag is None:
            self.command.insert(1, f'--{flag}')
        else:
            self.command[1] = f'--{flag}'
        self._flag = flag
    
    def remove_flag(self):
        """This method sets the flag to None and deletes it from the command pipe."""
        if self.flag is None:
            raise ValueError('There is no flag in the command pipe.')
        del self.command[1]
        self._flag = None

    def get_library(self, library: str) -> Type['Library']:
        """This method creates a Library class instance.
        Args:
            library: The name for a library (e.g. ta_morphometry).

        Returns:
            Library: A Library class instance.
        """
        library = Library(self, library)
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
    
    def run_command(self, *args, **kwargs) -> str:
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
        return result.stdout


class Library(SAGA):
    """This class represents a SAGA library.

    Parameters
    ----------
    SAGA : SAGA
        The parent SAGA instance.
    library : str
        The name of the SAGA library.

    Attributes
    ----------
    name : str
        The name of the SAGA library.

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

    def __init__(self, SAGA: SAGA, library: str):
        super().__init__(SAGA.command + [library])
        self.name = library
        
    def __str__(self):
        return self.run_command()

    def __repr__(self):
        return self.run_command()

    def get_tool(self, tool: str) -> Type['Tool']:
        """This method creates a Tool class instance.
        Args:
            tool: The name (index) of a tool inside the library (e.g. '17') that is shown inside square brackets
                when printing the Library object.

        Returns:
            Tool: A Tool class instance.
        """
        tool = Tool(self, tool)
        return tool


class Tool(SAGA):
    """This class represents a SAGA tool.

    Parameters
    ----------
    library : Library
        A Library class instance.
    tool : str
        The name (index) of a tool inside the library (e.g. '17') that is shown inside square brackets
                when printing the Library object.

    Attributes
    ----------
    tool : str
        The index of the SAGA tool inside the library.

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
    >>> saga_tool = saga_env.get_tool(library='ta_morphometry', tool='0')
    """

    def __init__(self, library: Library, tool: str):
        self.tool = tool
        super().__init__(library.command + [tool])

    def __str__(self):
        return self.run_command()

    def __repr__(self):
        return self.run_command()
