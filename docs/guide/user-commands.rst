=====================
User defined commands
=====================

.. |user_commands| replace:: :py:mod:`vpe.user_commands`
.. |CommandHandler| replace:: `vpe.CommandHandler`
.. |CommandInfo| replace:: `vpe.CommandInfo`
.. |command| replace:: `vpe.CommandHandler.command`
.. |define_command| replace:: `vpe.define_command`


Why user commands are tricky
============================

It is common for Vim plugin code to provide one ore more user defined commands
using Vim's :vim:`:command`. For plugins written in Python code,
:vim:`:command` can prove rather fiddly.

For example supposing you have '*myplugin*' and wish to provide a command that
takes 2 arguments and can operate on a range of lines. The function that
implements this functionality is '*some_module.do_frob*' and the command is
called '*Frob*'. You need to write some Python to format a Vim command something
like:

.. code-block:: vim

    :command -nargs -range Frob py3
    \   myplugin.some_module.do_frob(<f-args>, line1=<f-line1>)

And '*some_module.do_frob*' could be defined as:

.. code-block:: python

    def do_frob(*args: str, line1: int, line2: int):
        ...

Provided that '*some_module*' is exposed within the Vim Python namespace, this
will work, but there are some issues with the above approach.

1. Writing code to form the ``:command ...`` string is somewhat non-pythonic.

2. The need to refer to '*myplugin.some_module.do_frob*' is likely breaking the
   intended encapsulation of your code.

3. Different types of user command require different function signatures.

4. Creating a user command that invokes an instance method is even more tricky.

VPE provides a three mechanisms that make implementing user commands with
Python code much easier.

1. The |define_command| function, which is introduced in the next `section
   <sec_define_command>`.

2. The |CommandHandler| mix-in, which is covered `sec_command_handler`.

3. The |user_commands| module, which is covered `sec_user_commands` after.


.. _sec_define_command:

Function define_command
=======================

The |define_command| function provides the most basic support for user defined
commands. Using it, the earlier '*Frob*' example can be easily implemented within
'*some_module*' as:

.. code-block:: python

    import vpe

    def do_frob(info:vpe.CommandInfo, *args: str):
        # The range is in info.line1 and info.line2.
        ...

    vpe.define_command('Frob', do_frob, nargs='*')

- All command attributes are provided in the ``info`` parameter (avoiding problem
  3 above).

- The code in '*some_module*' does not need refer to '*myplugin*' or '*some_module*'
  itself (avoiding problem 2 above).

- There is not need to form a ``:command ...`` string (problem 1).

- Were '*do_frob*' an instance method, the code would still work as long as
  the instance is referenced (problem 4).

The |define_command| function takes a number of keyword arguments that are
analogues of the :vim:`:command` options with the same names.

nargs
    May be 0, 1, '\*', '?' or '+' ('0' and '1' as strings also work).

complete
    A string. Any value accepted by :vim:`:command`, except for 'custom' and
    'customlist' because these require a Vim function as an argument. If your
    command requires the complexity of a function for completion then I recommend
    using |user_commands| as described in `sec_user_commands`.

range
    Set to  ``True`` to simply allow the command to take a range. Use '%' to
    set a default range of the whole file and a number (may be as a string) to
    set a default count.

count
    The same as for :vim:`:command`, except that you can use integers or
    strings 'N'.

addr
    How special characters in a range are interpreted by Vim.

bang, bar, register, buffer
    Boolean values that act like the corresponding :vim:`:command` options.

The implementation of |define_command| invokes ``:command! ...`` so that any
previous command of the same name is replaced. The argument ``replace=False``
makes VPE invoke ``:command ...``, but I personally have found no good reason
to do this.


CommandInfo
-----------

The |CommandInfo| argument (parameter ``info`` of '*do_frob*' in the above
example) makes it easy for the called function to determine the details of how
the command was invoked. It provides the following attributes.

line1, line2
    The start line and end line of the command range.

range
    The number of items in the command range: 0, 1 or 2. This requires at least
    vim 8.0.1089; for earlier versions it is fixed as -1.

count
    Any count value supplied (see :vim:`command-count`).

bang
    True if the command was invoked with a '!'.

mods
    The command modifiers (see :vim:`:command-modifiers`). This is a space
    separated string.

reg
    The optional register, if provided.


Functions arguments
-------------------

Additional arguments can be passed to the command callback function. These are
defined using ``args`` and ``kwargs``.

.. code-block:: python

    def echo_command(info: vpe.CommandInfo, mode, *args, level=0):
        vpe.echo_msg(f'{mode}[{level}]: {" ".join(args)}')

    vpe.define_command(
        'Echo',
        echo_command,
        nargs='*',
        args=('warning',),
        kwargs={'level': 2})

The command:

.. code-block:: vim

    Echo 'The answer is' 30

Will print::

    warning[2]: The answer is 42

Notice that ``args`` preset using |define_command| are passed to the function
*before* the arguments provided to the ``Echo`` command.

The |CommandInfo| parameter can be suppressed if desired using the
``pass_info`` argument.

.. code-block:: python

    def echo_command(mode, *args, level=0):
        vpe.echo_msg(f'{mode}[{level}]: {args}')

    vpe.define_command(
        'Echo',
        echo_command,
        nargs='*',
        args=('info',),
        kwargs={'level': 2},
        pass_info=False)


.. _sec_command_handler:

The CommandHandler mix-in
=========================

In a similar way to key mapping, VPE provides a decorator approach to define
user commands, provided by the |CommandHandler| mix-in class. For example:

.. code-block:: python

    command = vpe.CommandHandler.command

    class MessageGenerator(vpe.CommandHandler):

        def __init__(self):
            self.auto_define_commands()

        @command('Echo', nargs='*', args=('info',), kwargs={'level': 2})
        def echo_command(self, mode, *args, level=0):
            vpe.echo_msg(f'{mode}[{level}]: {args}')

    message_gen = MessageGenerator()

In some circumstances, this can be a good alternative to using |define_command|.

Note that the mappings are only created when the ``self.auto_define_commands()``
method is invoked.  Also note that, by default, the methods do not receive a
|CommandInfo| object as the first argument. Give the |command| decorator a
``pass_info=True`` argument to change this behaviour.

The |command| decorator accepts all the arguments of |define_command| except
for ``func``.


.. _sec_user_commands:

The user_commands module
========================

.. note::

   Some details of this module may change before version 0.7 is released.

This module makes it easy to implement complex commands much more easily.
It is probably a bit harder to get up to speed with, but you can provide a much
richer user experience. Its features are:

- Support for subcommands, which can provide your plugin code with a much
  cleaner command line interface. For example, VPE itself provides one command,
  namely 'Vpe', but with a number of subcommands - 'log', 'version', *etc*.

- Command (and subcommand) help is automatically provided.

- The |user_commands| module also brings in the power of the standard Python
  ``argparse`` module. Providing easy support for:

  - Command line flags (such as ``--debug``).
  - Named mandatory and optional parameters.
  - Automatic argument parsing, checking and type conversion.

  Commands can make use of most of the features provided by the ``argparse``
  module.

- Command line Tab-key completion is automatically provided.

.. code-block:: python

    from argparse import Namespace
    from vpe.user_commands import (
        CommandHandler, SubcommandHandlerBase, TopLevelSubcommandHandler)

    class VPECommandProvider(TopLevelSubcommandHandler):
        """A class to provide some VPE support commands."""

        subcommands = {
            'log': (LogSubCommand, 'Log file management.'),
            'insert_config': (':simple', 'Insert the vpe_config global variable.'),
            'version': (':simple', 'Display the VPE version number.'),
        }

        def handle_insert_config(self, _args: Namespace) -> None:
            """Execute the 'Vpe insert_config' command."""
            ...

        def handle_version(self, _args: Namespace) -> None:
            """Execute the 'Vpe version' command."""
            echo_msg(f'VPE version {vpe.__version__}')

    _vpe_commands = VPECommandProvider('Vpe')

This creates the 'Vpe' user command, setting up an instance of
``VPECommandProvider`` to provide the command's implementation. The
``subcommands`` class level dictionary define the list of 'Vpe' subcommand
names, how each is implemented and a short message to be used in the generated
help.

Currently each subcommand can be implemented in one of two ways:

- For simple subcommands, by a method. In the example this is the case for the
  'log' and 'insert_config' subcommands. The implementation method is defined
  using the string ":simple" and actual method's name is formed as
  handle_<subcommand_name>. For example, the command 'Vpe version' will invoke
  the ``handle_version`` method.

- For subcommands, by a either a ``CommandHandler`` derived class or a
  ``SubcommandHandlerBase`` derived class. The latter is for subcommands which
  are in turn further composed of subcommands.

The 'Vpe log ...' subcommand is implemented by the ``LogSubCommand`` class.
This follows a similar pattern to ``VPECommandProvider``.

.. code-block:: python

    from vpe import core

    class LogSubCommand(SubcommandHandlerBase):
        """The 'log' sub-command support."""

        subcommands = {
            'show': (':simple', 'Show the log file buffer.'),
            'hide': (':simple', 'Hide the log file buffer.'),
            'length': (LogLengthCommand, 'Display/set the log file max length'),
            'redirect': (
                LogRedirectCommand, 'Display/set stdout/sterr redirection'),
        }

        def handle_show(self, _args: Namespace) -> None:
            """Handle the 'Vpe log show' command."""
            core.log.show()

        def handle_hide(self, _args: Namespace) -> None:
            """Handle the 'Vpe log hide' command."""
            core.log.hide()

Again, the simplest subcommands are implemented by methods. The others by
classes. The 'Vpe log length ...' command's code is:

.. code-block:: python

    class LogLengthCommand(CommandHandler):
        """The 'log length' sub-command support."""

        def add_arguments(self) -> None:
            """Add the arguments for this command."""
            self.parser.add_argument(
                'maxlen', type=int, nargs='?',
                help='New maximum length of the log.')

        def handle_command(self, args: Namespace):
            """Handle the 'Vpe log length' command."""
            if args.maxlen is None:
                echo_msg(f'VPE log maxlen = {core.log.maxlen}')
            else:
                core.log.set_maxlen(args.maxlen)

Although, at first glance, the above code examples may appear quite verbose it
is actually quite efficient. Notice, for example, that none of the code has to
perform any checking of the parameters, the |user_commands| and associated
``argparse`` code does all of that for you. The above examples allows all of
the following commands:

.. code-block:: vim

    " Show the VPE log in a split window. You can also use (non-ambigous)
    " abbreviations.
    Vpe log show
    Vp l s

    " Hide it again.
    Vpe log hide

    " Show the current VPE log max length. Then set it.
    Vpe log length
    Vpe log length 42

    " Show the VPE version
    Vpe version

    " Command and subcommand help.
    Vpe -h
    Vpe log length -h

And Tab-key completion comes for free. For example the key sequence 'Vp<tab>
l<tab> l<tab>' expands the command line to 'Vpe log length'.
