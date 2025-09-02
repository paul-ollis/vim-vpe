"""Support user commands based on Python's argparse module.

This module makes it easy to implement complex user commands. The features
provided are:

- Support for optional arguments.
- Clean implementation of subcommands.
- Subcommands, and options can be abbreviated.
- Automatic command line completion.
"""
from __future__ import annotations

import argparse
import functools
import inspect
import sys
from argparse import Namespace
from typing import ClassVar, Final, TYPE_CHECKING, Tuple, TypeAlias

from vpe import common, core, wrappers

if TYPE_CHECKING:
    from collections.abc import Sequence

SubcommandsTable: TypeAlias = dict[str, [Tuple['CommandHandler', str], str]]

#: Function to print single line error messages.
error_msg = functools.partial(core.error_msg, soon=True)

#: Debug control flag, for development only.
debug_completion: bool = False

#: A destination for help messages, only for testing.
help_dest: list[str] | None = None


class ArgumentError(argparse.ArgumentError):
    """Exception raised when a parse error occurs."""

    def __init__(self, message):
        super().__init__(argument=None, message=message)
        self.message = message.capitalize()

    def __str__(self):
        return self.message


class AmbiguousSubcommand(ArgumentError):
    """Exception raised when a subcommand is ambiguous."""

    def __init__(self, message, choices: list[str]):
        super().__init__(message=message)
        self.message = message
        self.choices = choices


class SubcommandReached(Exception):
    """Raised to indicate that a subcommand has been found."""

    def __init__(self, value: str):
        super().__init__()
        self.value = value


class HelpAction(argparse.Action):
    """A replacement for the standard argparse help action.

    This version defers the help output using `call_soon` and sets the parser's
    ``stop_processing`` flag.
    """
    def __init__(self,
                 option_strings,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help=None):                # pylint: disable=redefined-builtin
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        if not parser.no_help:
            parser.print_help(cmd_info=parser.command_handler.cmd_info)
            parser.stop_processing = True


class SubcommandAction(argparse.Action):
    """An action for subcommands."""

    def __init__(self,
                 option_strings,
                 subcommands_table: SubcommandsTable,
                 dest=None,
                 default=None,
                 help=None,
                 **_kwargs):                # pylint: disable=redefined-builtin
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=1,
            help=help)
        self.subcommand_info = {
            name: value[1] for name, value in subcommands_table.items()}

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        match, choices = unique_match(values[0], self.subcommand_info)
        if not match:
            if not choices:
                raise ArgumentError(f'Unrecognized subcommand {values[0]!r}')

            names = ', '.join(choices)
            msg = f'Ambiguous subcommand {values[0]!r}:'
            msg += f' could be any of {names}'
            raise AmbiguousSubcommand(msg, choices)

        setattr(namespace, self.dest, match)
        raise SubcommandReached(value=values[0])


class ArgumentParser(argparse.ArgumentParser):
    """A modified ArgumentParser designed to work with `CommandHandler`.

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
    """

    def __init__(
            self,
            command_handler: CommandHandler,
            command_name: str,
            *args, **kwargs,
        ):
        self.command_handler = command_handler
        self._completions = {}
        self.stop_processing = False
        self.no_help: bool = False

        # The next few lines prevent help using the default argparse help
        # action code and trying to exit Vim.
        add_help = kwargs.pop('add_help', True)
        kwargs['add_help'] = False
        kwargs['exit_on_error'] = False

        super().__init__(prog=command_name, *args, **kwargs)
        self._all_optionals = None
        self.popup: core.Popup | None = None

        # Add the help option only after we have been able to install our own
        # `HelpAction`.
        self.register('action', 'help', HelpAction)
        if add_help:
            self.add_argument(
                '-h', '--help',
                action='help', default=argparse.SUPPRESS,
                help='Show this help message.')
            self.add_help = True

    def parse_args(self, args: Sequence[str]):
        """Convert argument strings to attributes of the namespace."""
        # pylint: disable=arguments-differ, disable=signature-differs
        return super().parse_args(args=args, namespace=None)

    def parse_known_args(
            self, args=None, namespace=None, no_help: bool = False,
        ) -> tuple[Namespace, list[str]]:
        """Parse known arguments from the command line.

        This version does not try to sys.exit().

        As of Python 3.9.3, the exit_on_error initialisation argument does not
        work in the way expect.
        """
        self.stop_processing = False
        self.no_help = no_help
        return self.do_parse_known_args(args=args)

    def do_parse_known_args(
            self, args: Sequence[str],
        ) -> tuple[Namespace, list[str]]:
        """Parse known arguments, stopping at a subcommand.

        This is a modified version from the Python 3.11 standard library. This
        version stops processing arguments when a subcommand is encountered.
        The upshot is that optional arguments are get properly associated with
        the correct main command or subcommand.
        """
        args = list(args)
        namespace = argparse.Namespace()

        try:
            # Add any action defaults that aren't present.
            for action in self._actions:
                if action.dest is not argparse.SUPPRESS:
                    if not hasattr(namespace, action.dest):
                        if action.default is not argparse.SUPPRESS:
                            setattr(namespace, action.dest, action.default)

            # Parse the arguments.
            namespace, args = self._parse_known_args(args, namespace)

        except SubcommandReached as e:
            # The subcommand and preceding values need to be from the ``args``
            # variable.
            i = args.index(e.value)
            del args[:i + 1]

        return namespace, args

    def add_argument(self, *args, **kwargs):
        """Define how a single command-line argument should be parsed.

        This wraps the standard method in order to support command completion.
        """
        completions = kwargs.pop('completions', [])
        action = super().add_argument(*args, **kwargs)
        self._completions[action.dest] = completions
        return action

    def print_help(
            self,
            _file=None,
            cmd_info: common.CommandInfo | None = None,
        ) -> None:
        """Display the help message."""
        help_text = self.format_help()
        if help_text.startswith('usage: '):
            help_text = help_text.replace('usage:  ', 'usage: ', 1)
            help_text = help_text.replace('u', 'U', 1)

        if help_dest is not None:
            help_dest[:] = help_text.splitlines()
        elif cmd_info is not None and cmd_info.bang:         # pragma: no cover
            print(help_text)
            #print('\n'.join(self.format_help().splitlines()))
        else:                                                # pragma: no cover
            def make_popup():
                self.popup = core.PopupNotification(
                    help_text.splitlines(), 'Vpe_cmd_info',
                    highlight='MessageWindow')

            common.call_soon(make_popup)

    def format_help(self):
        # pylint: disable=protected-access
        self.usage = None
        usage_tail = self.format_usage()[7:]
        usage_head = self.command_handler.format_usage_head()
        usage = f'{usage_head} {usage_tail}'

        formatter = self._get_formatter()
        formatter.add_usage(
            usage, self._actions, self._mutually_exclusive_groups)
        formatter.add_text(self.description)
        lines = [formatter.format_help()]

        subcommands = self.command_handler.subcommand_help()
        if subcommands:
            lines.append('Subcommands:')
            for text in subcommands:
                lines.append(f'   {text}')

        formatter = self._get_formatter()
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(
                [action for action in action_group._group_actions
                if not isinstance(action, SubcommandAction)])
            formatter.end_section()
        formatter.add_text(self.epilog)
        lines.append(formatter.format_help())

        return '\n'.join(lines)

    def error(self, message):
        """Raise an ArgumentError."""
        raise ArgumentError(str(message))

    def exit(self, status=0, message=None):              # pragma: unreachable
        """Raise ArgumentError."""
        raise ArgumentError(message)

    def get_completions(self, arglead: str) -> list[str]:
        """Get the possible completions for a partial command.

        :arglead: The partial argument to be completed.
        :return:   A list of possible completion strings.
        """
        # Build up the list of all optional flags the first time this is
        # invoked.
        if self._all_optionals is None:
            self._all_optionals = []
            for action in self._actions:
                self._all_optionals.extend(action.option_strings)
            self._all_optionals.sort()

        if arglead:
            _, choices = unique_match(arglead, self._all_optionals)
        else:
            choices = list(self._all_optionals)
        return choices


class CommandHandler:
    """A class providing a Vim user command or subcommand."""

    def __init__(
            self,
            command_name: str,
            parent: CommandHandler | None,
        ):
        self.command_name = command_name
        self.parent: CommandHandler = parent
        self.parser: ArgumentParser = self.create_parser()
        self.cmd_info: common.CommandInfo | None = None
        self.args: Namespace | None = None
        self.add_arguments()

    def create_parser(self) -> ArgumentParser:
        """Create the argument parser for this command."""
        return ArgumentParser(self, command_name=self.command_name)

    def add_arguments(self) -> None:
        """Add the arguments for this command."""

    def process_command(
            self,
            cmd_info: common.CommandInfo,
            vim_cmd_args: tuple[str],
        ) -> None:
        """Process this command or subcommand.

        :cmd_info:
            Information about the Vpe command, such as counts or line ranges.
        :subcommands:
            The sequence of subcommands leading to and in including this
            subcommand. When the subclass is a SimpleCommandHandler this has
            zero length.
        :vim_cmd_args:
            The command and arguments that Vim has parsed from the command
            line.
        """
        self.cmd_info = cmd_info
        try:
            self.args = self.parser.parse_args(vim_cmd_args)
        except ArgumentError as e:
            error_msg(e)
        else:
            self.handle_command(self.args)

    def get_completions(
            self, _vim_args: list[str], _at_new_arg: bool, arglead: str,
        ) -> list[str]:
        """Attempt command line completion for this command.

        :vim_args:
            The vim command line arguments that are before the cursor.
        :at_new_arg:
            True if the cursor's position is where a new argument/subcommand
            should be inserted.
        :return:
            A list strings representing the possible completions.
        """
        completions = self.parser.get_completions(arglead)
        return completions

    def handle_command(self, args: Namespace):
        """Handle this command."""

    def subcommand_help(self) -> list[str]:
        """Provide subcommand help as a list of strings."""
        return []

    def format_usage_head(self) -> str:
        """Format the leading part of a usage message."""
        if self.parent:
            # pylint: disable=protected-access
            return self.parent._format_usage_head()
        else:
            return ''

    def _format_usage_head(self) -> str:
        """Format the leading part of a usage message."""
        if self.parent:
            # pylint: disable=protected-access
            return f'{self.parent._format_usage_head()} {self.command_name}'
        else:
            return self.command_name

class SubcommandHandlerBase(CommandHandler):
    """Base for a command that has subcommands."""

    subcommands: SubcommandsTable = {}

    def __init__(
            self,
            command_name: str,
            parent: SubcommandHandlerBase | None,
        ):
        super().__init__(command_name, parent)
        action = functools.partial(
            SubcommandAction, subcommands_table=self.subcommands)
        if self.subcommands:
            self.parser.add_argument(
                'subcommand', nargs='?', action=action, help='Subcommand name')
        self.cmd_vector: SubcommandsTable = {}
        self._init_sub_commands()

    def process_command(                    # pylint: disable=too-many-branches
            self,
            cmd_info: common.CommandInfo,
            vim_cmd_args: tuple[str],
        ) -> None:
        """Process this command or subcommand.

        :cmd_info:
            Information about the Vpe command, such as counts or line ranges.
        :vim_cmd_args:
            The command and arguments that Vim has parsed from the command
            line.
        """
        # Parse the arguments for this command. The first positional
        # argument will be a subcommand or not present. Any following
        # positional arguments will be for the subcommand itself.
        self.cmd_info = cmd_info
        try:
            result = self.parser.parse_known_args(vim_cmd_args)
        except ArgumentError as e:
            error_msg(e)
            self.parser.stop_processing = True
        else:
            self.args, unparsed_args = result
        if self.parser.stop_processing:
            return

        subcommand = self.args.subcommand if self.subcommands else None
        if subcommand is not None:
            subcommand, partials = unique_match(subcommand, self.cmd_vector)
            # I believe that following block is probably not needed, but I
            # cannot rule out some (mis)use of the stdlib argparse library
            # proving me wrong.
            if subcommand:
                handler = self.cmd_vector.get(subcommand)
                if handler is None:                      # pragma: unreachable
                    error_msg('Invalid subcommand {subcommand}')
                    return
            elif partials:                               # pragma: unreachable
                compl = ' '.join(partials)
                error_msg(
                    'Ambiguous subcommand {subcommand}'
                    f' completions = {compl}'
                )
                return
            else:                                        # pragma: unreachable
                error_msg(f'Invalid subcommand {subcommand}')
                return

            if isinstance(handler, SubcommandHandlerBase):
                handler.process_command(cmd_info, unparsed_args)
            elif isinstance(handler, CommandHandler):
                handler.process_command(cmd_info, unparsed_args)
            else:
                if unparsed_args:
                    extra_args = ' '.join(unparsed_args)
                    error_msg(f'Unexpected arguments: {extra_args}')
                else:
                    handler(self.args)

        else:
            if unparsed_args:
                extra_args = ' '.join(unparsed_args)
                error_msg(f'Unexpected arguments: {extra_args}')
            else:
                self.handle_no_subcommand(cmd_info, self.args)

    def get_completions(
            self, vim_args: list[str], at_new_arg: bool, arglead: str,
        ) -> list[str]:
        """Attempt command line completion for this command.

        :vim_args:
            The vim command line arguments that are before the cursor.
        :at_new_arg:
            True if the cursor's position is where a new argument/subcommand
            should be inserted.
        :return:
            A list strings representing the possible completions.
        """
        # Use normal parsing to dig down to the correct subcommand.
        try:
            result = self.parser.parse_known_args(vim_args, no_help=True)

        except AmbiguousSubcommand as e:
            # The completions are the choices stored in the exception.
            return e.choices

        except ArgumentError:
            return []

        else:
            self.args, unparsed_args = result

        if self.parser.stop_processing:                  # pragma: unreachable
            return []

        try:
            subcommand = None if self.args is None else self.args.subcommand
        except AttributeError:
            subcommand = None
        if subcommand is not None:
            if len(unparsed_args) == 0 and vim_args and not at_new_arg:
                if vim_args[0] != subcommand:
                    # We have a unique, but partial subcommand.
                    return [subcommand]

            # We need to drill down into the subcommand for completions.
            handler = self.cmd_vector.get(subcommand)
            return handler.get_completions(unparsed_args, at_new_arg, arglead)

        # Give the argument parser a chance to provide completions. These will
        # not include valid subcommands.
        completions = self.parser.get_completions(arglead)

        # Add in any subcommands names that match the argument lead.
        if at_new_arg:
            completions[0:0] = list(self.cmd_vector)
        elif not arglead.startswith('-'):                # pragma: unreachable
            # TODO: Unreachable?
            _, choices = unique_match(arglead, self.cmd_vector)
            completions[0:0] = choices

        return completions

    def handle_no_subcommand(
            self,
            cmd_info: common.CommandInfo,
            args: Namespace,
        ):
        """Handle the case of no subcommand being provided."""
        error_msg('Missing subcommand')

    def subcommand_help(self) -> list[str]:
        """Provide subcommand help as a list of strings."""
        names = list(self.subcommands)
        w = max((len(n) for n in names), default=0)
        return [
            f'{command:{w}} - {help}'
            for command, (_, help) in sorted(self.subcommands.items())]

    def _init_sub_commands(self) -> None:
        """Recursively build subcommands."""
        handler_spec: str | SubcommandHandlerBase
        for name, (handler_spec, _help_text) in self.subcommands.items():
            if handler_spec == ':simple':
                self.cmd_vector[name] = getattr(self, f'handle_{name}')
            else:
                self.cmd_vector[name] = handler_spec(name, self)


class VimCommandHandler:
    """Base for user defined Vim commands."""
    registered_commands: ClassVar[SubcommandsTable] = {}
    allow_bang: Final[ClassVar[bool]] = True
    allow_register: Final[ClassVar[bool]] = False
    range: Final[ClassVar[bool | int | str]] = ''
    count: Final[ClassVar[int | str]] = ''

    def __init__(self, command_name: str, *args, **kwargs):
        super().__init__(command_name, *args, **kwargs)
        self.registered_commands[command_name] = self
        self._init_completion()
        core.define_command(
            command_name, self.handle_main_command,
            nargs='*',
            complete='customlist,VPE_Command_Complete',
            bar=True,
            count=self.count,
            range=self.range,
            register=self.allow_register,
            bang=self.allow_bang)

    @staticmethod
    def _init_completion() -> None:
        """Perform additional initialisation for completion support.

        This creates a Vim function the first time it is invoked. Subsequent
        calls do nothing.
        """
        if not wrappers.vim.exists('*VPE_Command_Complete'):
            wrappers.commands.py3('import vpe.vpe_commands')
            wrappers.vim.command(inspect.cleandoc("""
                function! VPE_Command_Complete(ArgLead, CmdLine, CursorPos)
                    let g:_vpe_args_ = {}
                    let g:_vpe_args_['arglead'] = a:ArgLead
                    let g:_vpe_args_['cmdline'] = a:CmdLine
                    let g:_vpe_args_['cursorpos'] = a:CursorPos
                    let expr = 'vpe.user_commands.VimCommandHandler.complete()'
                    return py3eval(expr)
                endfunction
            """))

    def handle_main_command(
            self, cmd_info: common.CommandInfo, *vim_cmd_args: str):
        """Parse and execute the main command.

        This is invoked by Vim when the user enters this command plus one or
        more arguments.

        :cmd_info:
            Information about the Vpe command, such as counts or line ranges.
        :vim_cmd_args:
            The command and arguments that Vim has parsed from the command
            line.
        """

    @classmethod
    def complete(cls) -> list[str]:
        """Attempt command line completion for a command.

        :return:
            A list strings representing the possible completions.
        """
        try:
            vim_args = dict(getattr(wrappers.vim.vars, '_vpe_args_'))
            arglead = vim_args['arglead']
            cmdline = vim_args['cmdline']
            pos = vim_args['cursorpos']

            # Get the command at the start of the line, which may only be
            # partial. Find its completion and hence the command handler.
            command_name, _, _ = cmdline.partition(' ')
            command, _ = unique_match(command_name, cls.registered_commands)
            handler = cls.registered_commands.get(command)
            if handler is None:
                return []

            if debug_completion:
                print(
                    f'Perform completion for {command}'
                    f' {handler.__class__.__name__}')

            # Get the argument text before the cursor and figure out if we have
            # a partial argument or not.
            before_cursor, _ = cmdline[:pos], cmdline[pos:]
            _, _, before_cursor = before_cursor.partition(' ')
            vim_args = before_cursor.split()
            at_new_arg = before_cursor.endswith(' ')
            if len(vim_args) == 0:
                # For some reason, Vim suppresses the first space after the
                # command name. So we infer that if we have zero arguments then
                # we must be at a new argument.
                at_new_arg = True
            if debug_completion:
                print(f'   {arglead=}')
                print(f'   {vim_args=}')
                print(f'   {at_new_arg=}')
            return handler.get_completions(vim_args, at_new_arg, arglead)

        # This code is probably unreachable, but I am happier to be defensive
        # here. Possible exceptions are undefined, so we treat all exceptions
        # as a
        # simple completion failure.
        except Exception as e:                           # pragma: unreachable
            # pylint: disable=broad-except
            core.error_msg("Vpe command completion error:", e)
            print("Vpe command completion error:", e)

        return []                                        # pragma: unreachable


class SimpleCommandHandler(VimCommandHandler, CommandHandler):
    """A top-level user defined Vim command.

    This provides the main parser for a command that has subcommands.
    """

    def __init__(self, command_name: str):
        super().__init__(command_name=command_name, parent=None)

    def handle_main_command(
            self, cmd_info: common.CommandInfo, *vim_cmd_args: str):
        super().process_command(cmd_info, vim_cmd_args)


class TopLevelSubcommandHandler(VimCommandHandler, SubcommandHandlerBase):
    """A top-level user defined Vim command, with subcommands.

    This provides the main parser for a command that has subcommands.
    """

    def __init__(self, command_name: str):
        super().__init__(command_name=command_name, parent=None)

    def handle_main_command(
            self, cmd_info: common.CommandInfo, *vim_cmd_args: str):
        super().process_command(cmd_info, vim_cmd_args)

    def create_parser(self) -> ArgumentParser:
        """Create the subcommand argument parser for this command."""
        parser = super().create_parser()
        return parser


def unique_match(text: str, choices: list[str]) -> tuple[str, list[str]]:
    """Try to find a unique match within choices that starts with text.

    :text:
        The text to match.
    :choices:
        The choices from which to select the match.
    :return:
        A tuple of (match, matches). The ``match`` is an empty string if no
        unique match was found, in which case ``matches`` is a, possibly empty,
        list of partial matches.
    """
    choices = sorted(choices)
    matches = [v for v in choices if v.startswith(text)]
    if matches and (matches[0] == text or len(matches) == 1):
        return matches[0], matches
    return '', matches
