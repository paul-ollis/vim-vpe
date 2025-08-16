Module vpe.argparse
===================


.. py:module:: argparse

Support user commands based on Python's argparse module.

This module makes it easy to implement user complex user commands. The features
provided are:

- Support for optional arguments.
- Clean implementation of subcommands.
- Subcommands, and options can be abbreviated.
- Automatic command line completion.

.. rubric:: AmbiguousSubcommand

.. py:class:: AmbiguousSubcommand(message,choices: list[str])

    Exception raised when a subcommand is ambiguous.

.. rubric:: ArgumentError

.. py:class:: ArgumentError(message)

    Exception raised when a parse error occurs.

.. rubric:: ArgumentParser

.. py:class:: ArgumentParser(...)

    .. code::

        ArgumentParser(
                command_handler: CommandHandler,
                command_name: str,
                *args,

    A modified ArgumentParser designed to work with `CommandHandler`.

    This is fairly thin wrapper around the standard library argparse's
    ArgumentParser. The changes are:

    - The parse_args and parse_known_args methods do not try to invoke
      sys.exit().
    - It has support for partial command completions that work the way I
      expect.
    - The word 'prog' is generally replaced by 'command_name', just to be
      consistent with `CommandHandler` and its subclasses.
    - Parser defaults are not supported (those set by ``set_defaults``).
      Defaults have to be specified as part of ``add_argument``.

    **Methods**

        .. py:method:: add_argument(*args,**kwargs)

            Define how a single command-line argument should be parsed.

            This wraps the standard method in order to support command completion.

        .. py:method:: do_parse_known_args(args: Sequence[str]) -> tuple[Namespace, list[str]]

            Parse known arguments, stopping at a subcommand.

            This is a modified version from the Python 3.11 standard library. This
            version stops processing arguments when a subcommand is encountered.
            The upshot is that optional arguments are get properly associated with
            the correct main command or subcommand.

        .. py:method:: error(message)

            Raise an ArgumentError.

        .. py:method:: exit(status=0,message=None)

            Raise ArgumentError.

        .. py:method:: get_completions(arglead: str) -> list[str]

            Get the possible completions for a partial command.


            **Parameters**

            .. container:: parameters itemdetails

                *arglead*: str
                    The partial argument to be completed.

            **Return value**

            .. container:: returnvalue itemdetails

                A list of possible completion strings.

        .. py:method:: parse_args(args: Sequence[str])

            Convert argument strings to attributes of the namespace.

        .. py:method:: parse_known_args(...)

            .. code::

                parse_known_args(
                        args=None,
                        namespace=None,
                        no_help: bool = False

            Parse known arguments from the command line.

            This version does not try to sys.exit().

            As of Python 3.9.3, the exit_on_error initialisation argument does not
            work in the way expect.

        .. py:method:: print_help(...)

            .. code::

                print_help(
                        _file=None,
                        cmd_info: common.CommandInfo | None = None

            Display the help message.

.. rubric:: CommandHandler

.. py:class:: CommandHandler(command_name: str,parent: CommandHandler | None)

    A class providing a Vim user command or subcommand.

    **Methods**

        .. py:method:: add_arguments() -> None

            Add the arguments for this command.

        .. py:method:: create_parser() -> ArgumentParser

            Create the argument parser for this command.

        .. py:method:: format_usage_head() -> str

            Format the leading part of a usage message.

        .. py:method:: get_completions(...)

            .. code::

                get_completions(
                        _vim_args: list[str],
                        _at_new_arg: bool,
                        arglead: str

            Attempt command line completion for this command.


            **Parameters**

            .. container:: parameters itemdetails

                *vim_args*
                    The vim command line arguments that are before the cursor.
                *at_new_arg*
                    True if the cursor's position is where a new argument/subcommand
                    should be inserted.

            **Return value**

            .. container:: returnvalue itemdetails

                A list strings representing the possible completions.

        .. py:method:: handle_command(args: Namespace)

            Handle this command.

        .. py:method:: process_command(...)

            .. code::

                process_command(
                        cmd_info: common.CommandInfo,
                        vim_cmd_args: tuple[str]

            Process this command or subcommand.


            **Parameters**

            .. container:: parameters itemdetails

                *cmd_info*: CommandInfo
                    Information about the Vpe command, such as counts or line ranges.
                *subcommands*
                    The sequence of subcommands leading to and in including this
                    subcommand. When the subclass is a SimpleCommandHandler this has
                    zero length.
                *vim_cmd_args*: tuple
                    The command and arguments that Vim has parsed from the command
                    line.

        .. py:method:: subcommand_help() -> list[str]

            Provide subcommand help as a list of strings.

.. rubric:: HelpAction

.. py:class:: HelpAction(...)

    .. code::

        HelpAction(
                option_strings,
                dest='==SUPPRESS==',
                default='==SUPPRESS==',

    A replacement for the standard argparse help action.

    This version defers the help output using `call_soon` and sets the parser's
    ``stop_processing`` flag.

.. rubric:: SimpleCommandHandler

.. py:class:: SimpleCommandHandler(command_name: str)

    A top-level user defined Vim command.

    This provides the main parser for a command that has subcommands.

.. rubric:: SubcommandAction

.. py:class:: SubcommandAction(...)

    .. code::

        SubcommandAction(
                option_strings,
                subcommands_table: SubcommandsTable,
                dest=None,
                default=None,
                help=None,

    An action for subcommands.

.. rubric:: SubcommandHandlerBase

.. py:class:: SubcommandHandlerBase(command_name: str,parent: SubcommandHandlerBase | None)

    Base for a command that has subcommands.

    **Methods**

        .. py:method:: get_completions(...)

            .. code::

                get_completions(
                        vim_args: list[str],
                        at_new_arg: bool,
                        arglead: str

            Attempt command line completion for this command.


            **Parameters**

            .. container:: parameters itemdetails

                *vim_args*: list
                    The vim command line arguments that are before the cursor.
                *at_new_arg*: bool
                    True if the cursor's position is where a new argument/subcommand
                    should be inserted.

            **Return value**

            .. container:: returnvalue itemdetails

                A list strings representing the possible completions.

        .. py:method:: handle_no_subcommand(cmd_info: common.CommandInfo,args: Namespace)

            Handle the case of no subcommand being provided.

        .. py:method:: process_command(...)

            .. code::

                process_command(
                        cmd_info: common.CommandInfo,
                        vim_cmd_args: tuple[str]

            Process this command or subcommand.


            **Parameters**

            .. container:: parameters itemdetails

                *cmd_info*: CommandInfo
                    Information about the Vpe command, such as counts or line ranges.
                *vim_cmd_args*: tuple
                    The command and arguments that Vim has parsed from the command
                    line.

        .. py:method:: subcommand_help() -> list[str]

            Provide subcommand help as a list of strings.

.. rubric:: SubcommandReached

.. py:class:: SubcommandReached(value: str)

    Raised to indicate that a subcommand has been found.

.. rubric:: TopLevelSubcommandHandler

.. py:class:: TopLevelSubcommandHandler(command_name: str)

    A top-level user defined Vim command, with subcommands.

    This provides the main parser for a command that has subcommands.

    **Methods**

        .. py:method:: create_parser() -> ArgumentParser

            Create the subcommand argument parser for this command.

.. rubric:: VimCommandHandler

.. py:class:: VimCommandHandler(command_name: str,*args,**kwargs)

    Base for user defined Vim commands.

    **Methods**

        .. py:method:: handle_main_command(cmd_info: common.CommandInfo,*vim_cmd_args: str)

            Parse and execute the main command.

            This is invoked by Vim when the user enters this command plus one or
            more arguments.

            **Parameters**

            .. container:: parameters itemdetails

                *cmd_info*: CommandInfo
                    Information about the Vpe command, such as counts or line ranges.
                *vim_cmd_args*: str
                    The command and arguments that Vim has parsed from the command
                    line.

    **Class methods**

        .. py:classmethod:: complete() -> list[str]

            Attempt command line completion for a command.


            **Return value**

            .. container:: returnvalue itemdetails

                A list strings representing the possible completions.

.. rubric:: unique_match

.. py:function:: unique_match(text: str,choices: list[str]) -> tuple[str, list[str]]

    Try to find a unique match within choices that starts with text.


    **Parameters**

    .. container:: parameters itemdetails

        *text*: str
            The text to match.
        *choices*: list
            The choices from which to select the match.

    **Return value**

    .. container:: returnvalue itemdetails

        A tuple of (match, matches). The ``match`` is an empty string if no
        unique match was found, in which case ``matches`` is a, possibly empty,
        list of partial matches.
