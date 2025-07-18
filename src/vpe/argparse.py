"""Thin wrapper around the standard argparse module.

This modifies the standard library argparse as follows:

- Prevents calls to sys.exit() during argument parsing, when the exit_on_error
  option is cleared. (As of Python 3.9.3) the exit_on_error construction
  argument does not not seem to work correctly.)
- Adds support for partial command completion.
- Adds the SubcommandParser, which extends support for command completion
  with subcommands.
"""
from __future__ import annotations

# TODO: Make this a separate plug-in
#
#       Note that this is from the subcmd pluing within vpe_plugins.

import argparse
import functools
import inspect
import sys
from typing import ClassVar, TYPE_CHECKING, Type, TypeAlias, Union

from vpe import commands, common, core, wrappers

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Sequence

SubcommandsTable: TypeAlias = dict[str, tuple[Union['CommandBase', str], str]]

#: Function to print single line error messages.
error_msg = functools.partial(core.error_msg, soon=True)

#: Decorator for `TopLevelSubCommandHandler` methods that implement commands.
command_handler = functools.partial(
    core.CommandHandler.command,
    nargs='+',
    complete='customlist,VPE_Command_Complete',
    bar=True,
)


class ArgumentError(argparse.ArgumentError):
    """Exception raised when a parse error occurs."""

    def __init__(self, message):
        super().__init__(argument=None, message=message)
        self.message = message

    def __str__(self):
        return self.message


class Stop(Exception):
    """Raised to prevent further processing."""


class HelpAction(argparse.Action):
    """A replacement for the standard argparse help action."""

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
        print(f'HI: {namespace=} {values=} {option_string=}')
        common.call_soon(parser.print_help)
        parser.result = 'displayed_help'
        raise Stop()


class SubcommandAction(argparse.Action):
    """An action for subcommands."""

    def __init__(self,
                 option_strings,
                 subcommands_table: SubcommandsTable,
                 dest='__subcommand__',
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
        parser.stop_collecting = True
        setattr(namespace, '__subcommand__', values[0])


class ArgumentParser(argparse.ArgumentParser):
    """A modified argparse.ArgumentParser.

    This is fairly thin wrapper around the standard library argparse's
    ArgumentParser. The changes are:

    - The parse_args and parse_known_args methods do not try to invoke
      sys.exit() when exit_on_error is False.
    - It has support for partial command completions that work the way I
      expect.
    - Some features that do not make sense within the Vim environment, such
      as reading arguments from files) are disabled.
    - The word 'prog' is generally replaced by 'command_name'.
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(
            self, command_name: str, *args,
            parent: ArgumentParser | None = None, **kwargs,
        ):
        self._completions = {}
        self._get_completions = {}

        # The next 2 lines prevent help using the default argparse help action
        # code.
        add_help = kwargs.pop('add_help', True)
        kwargs['add_help'] = False

        super().__init__(prog=command_name, *args, **kwargs)
        self.parent = parent
        self._parsing_in_progress = 0
        self._all_optionals = None
        self.exit_on_error = kwargs.get('exit_on_error', True)
        self.result: str = ''
        self.popup: core.Popup | None = None
        self.register('action', 'help', HelpAction)
        self.stop_collecting = False
        self.subcommands_table = {}

        # Add the help option only after we have been able to install our own
        # `HelpAction`.
        if add_help:
            self.add_argument(
                '-h', '--help',
                action='help', default=argparse.SUPPRESS,
                help='show this help message and exit')
            self.add_help = True

    # TODO: Should this be supported?
    def parse_args(self, args: Sequence[str]):
        """Convert argument strings to attributes of the namespace."""
        # pylint: disable=arguments-differ, disable=signature-differs
        self.result = ''
        self._parsing_in_progress += 1
        try:
            return super().parse_args(args=args, namespace=None)
        finally:
            self._parsing_in_progress -= 1

    def parse_known_args(self, args=None, namespace=None):
        """Version that does not try to sys.exit() when disabled.

        As of Python 3.9.3, the exit_on_error initialisation argument does not
        work correctly.
        """
        self.stop_collecting = False
        self._parsing_in_progress += 1
        try:
            return self.do_parse_known_args(args=args)
        finally:
            self._parsing_in_progress -= 1

    def do_parse_known_args(self, args: Sequence[str]):
        """Parse known arguments, stopping at a sub-command.

        This is a modified version from the Python 3.11 standard library. The
        changes are:

        - Reading arguments from a file is not supported.
        """
        args = list(args)
        namespace = argparse.Namespace()

        # Add any action defaults that aren't present.
        for action in self._actions:
            if action.dest is not argparse.SUPPRESS:
                if not hasattr(namespace, action.dest):
                    if action.default is not argparse.SUPPRESS:
                        setattr(namespace, action.dest, action.default)

        # Add any parser defaults that aren't present.
        for dest, default_value in self._defaults.items():
            if not hasattr(namespace, dest):
                setattr(namespace, dest, default_value)

        # Parse the arguments.
        if self.exit_on_error:
            try:
                namespace, args = self._parse_known_args(args, namespace)
            except ArgumentError as err:
                self.error(str(err))
        else:
            namespace, args = self._parse_known_args(args, namespace)

        # pylint: disable=protected-access
        if hasattr(namespace, argparse._UNRECOGNIZED_ARGS_ATTR):
            args.extend(getattr(namespace, argparse._UNRECOGNIZED_ARGS_ATTR))
            delattr(namespace, argparse._UNRECOGNIZED_ARGS_ATTR)
        return namespace, args

    def _parse_known_args(self, arg_strings, namespace):
        # pylint: disable=too-many-branches,too-many-locals,too-many-statements
        # pylint: disable=protected-access

        # Map all mutually exclusive arguments to the other arguments they
        # cannot occur with.
        action_conflicts = {}
        for mutex_group in self._mutually_exclusive_groups:
            group_actions = mutex_group._group_actions
            for i, mutex_action in enumerate(mutex_group._group_actions):
                conflicts = action_conflicts.setdefault(mutex_action, [])
                conflicts.extend(group_actions[:i])
                conflicts.extend(group_actions[i + 1:])

        # Find all option indices, and determine the arg_string_pattern which
        # has an 'O' if there is an option at an index, an 'A' if there is an
        # argument, or a '-' if there is a '--'.
        option_string_indices = {}
        arg_string_pattern_parts = []
        arg_strings_iter = iter(arg_strings)
        for i, arg_string in enumerate(arg_strings_iter):

            # All args after -- are non-options
            if arg_string == '--':
                arg_string_pattern_parts.append('-')
                for arg_string in arg_strings_iter:
                    arg_string_pattern_parts.append('A')

            # Otherwise, add the arg to the arg strings and note the index if
            # it was an option.
            else:
                option_tuple = self._parse_optional(arg_string)
                if option_tuple is None:
                    pattern = 'A'
                else:
                    option_string_indices[i] = option_tuple
                    pattern = 'O'
                arg_string_pattern_parts.append(pattern)

        # Join the pieces together to form the pattern.
        arg_strings_pattern = ''.join(arg_string_pattern_parts)

        # Converts arg strings to the appropriate and then take the action.
        seen_actions = set()
        seen_non_default_actions = set()

        def take_action(action, argument_strings, option_string=None):
            seen_actions.add(action)
            argument_values = self._get_values(action, argument_strings)

            # Generate an error if this argument is not allowed with other
            # previously seen arguments, assuming that actions that use the
            # default value don't really count as "present".
            if argument_values is not action.default:
                seen_non_default_actions.add(action)
                for conflict_action in action_conflicts.get(action, []):
                    if conflict_action in seen_non_default_actions:
                        msg = 'not allowed with argument %s'
                        action_name = argparse._get_action_name(conflict_action)
                        raise argparse.ArgumentError(action, msg % action_name)

            # Take the action if we didn't receive a SUPPRESS value (e.g. from
            # a default).
            if argument_values is not argparse.SUPPRESS:
                action(self, namespace, argument_values, option_string)

        def consume_optional(start_index):
            """Convert arg_strings into an optional action."""

            # Get the optional identified at this index.
            option_tuple = option_string_indices[start_index]
            action, option_string, explicit_arg = option_tuple

            # Identify additional optionals in the same arg string (e.g. -xyz
            # is the same as -x -y -z if no args are required)
            match_argument = self._match_argument
            action_tuples = []
            while True:

                # If we found no optional action, skip it.
                if action is None:
                    extras.append(arg_strings[start_index])
                    return start_index + 1

                # If there is an explicit argument, try to match the
                # optional's string arguments to only this.
                if explicit_arg is not None:
                    arg_count = match_argument(action, 'A')

                    # If the action is a single-dash option and takes no
                    # arguments, try to parse more single-dash options out of
                    # the tail of the option string
                    chars = self.prefix_chars
                    if (
                        arg_count == 0
                        and option_string[1] not in chars
                        and explicit_arg != ''
                    ):
                        action_tuples.append((action, [], option_string))
                        char = option_string[0]
                        option_string = char + explicit_arg[0]
                        new_explicit_arg = explicit_arg[1:] or None
                        optionals_map = self._option_string_actions
                        if option_string in optionals_map:
                            action = optionals_map[option_string]
                            explicit_arg = new_explicit_arg
                        else:
                            msg = 'ignored explicit argument %r'
                            raise argparse.ArgumentError(
                                action, msg % explicit_arg)

                    # If the action expects exactly one argument, we've
                    # successfully matched the option; exit the loop.
                    elif arg_count == 1:
                        stop = start_index + 1
                        args = [explicit_arg]
                        action_tuples.append((action, args, option_string))
                        break

                    # Error if a double-dash option did not use the explicit
                    # argument
                    else:
                        msg = 'ignored explicit argument %r'
                        raise argparse.ArgumentError(
                            action, msg % explicit_arg)

                # If there is no explicit argument, try to match the optional's
                # string arguments with the following strings if successful,
                # exit the loop.
                else:
                    start = start_index + 1
                    selected_patterns = arg_strings_pattern[start:]
                    arg_count = match_argument(action, selected_patterns)
                    stop = start + arg_count
                    args = arg_strings[start:stop]
                    action_tuples.append((action, args, option_string))
                    break

            # Add the Optional to the list and return the index at which the
            # Optional's string args stopped.
            assert action_tuples
            for action, args, option_string in action_tuples:
                take_action(action, args, option_string)
            return stop

        # The list of Positionals left to be parsed; this is modified by
        # consume_positionals().
        positionals = self._get_positional_actions()

        def consume_positionals(start_index):
            """Convert as many positionals as possible into actions."""

            # Match as many Positionals as possible.
            match_partial = self._match_arguments_partial
            selected_pattern = arg_strings_pattern[start_index:]
            arg_counts = match_partial(positionals, selected_pattern)

            # Slice off the appropriate arg strings for each Positional and add
            # the Positional and its args to the list.
            for action, arg_count in zip(positionals, arg_counts):
                args = arg_strings[start_index: start_index + arg_count]
                start_index += arg_count
                take_action(action, args)

            # Slice off the Positionals that we just parsed and return the
            # index at which the Positionals' string args stopped.
            positionals[:] = positionals[len(arg_counts):]
            return start_index

        # Consume Positionals and Optionals alternately, until we have passed
        # the last option string.
        extras = []
        start_index = 0
        if option_string_indices:
            max_option_string_index = max(option_string_indices)
        else:
            max_option_string_index = -1
        while start_index <= max_option_string_index:

            # Consume any positionals preceding the next option.
            next_option_string_index = min(
                index
                for index in option_string_indices
                if index >= start_index)
            if start_index != next_option_string_index:
                positionals_end_index = consume_positionals(start_index)

                # Only try to parse the next optional if we didn't consume the
                # option string during the positionals parsing.
                if positionals_end_index > start_index:
                    start_index = positionals_end_index
                    continue

                start_index = positionals_end_index

            # If the stop_collecting flag is set then all remaining aruments
            # are extras.
            if self.stop_collecting:
                break

            # If we consumed all the positionals we could and we're not at the
            # index of an option string, there were extra arguments.
            if start_index not in option_string_indices:
                strings = arg_strings[start_index:next_option_string_index]
                extras.extend(strings)
                start_index = next_option_string_index

            # Consume the next optional and any arguments for it.
            start_index = consume_optional(start_index)

        # Consume any positionals following the last Optional.
        stop_index = consume_positionals(start_index)

        # If we didn't consume all the argument strings, there were extras.
        extras.extend(arg_strings[stop_index:])

        # Make sure all required actions were present and also convert action
        # defaults which were not given as arguments.
        required_actions = []
        for action in self._actions:
            if action not in seen_actions:
                if action.required:
                    required_actions.append(argparse._get_action_name(action))
                else:
                    # Convert action default now instead of doing it before
                    # parsing arguments to avoid calling convert functions
                    # twice (which may fail) if the argument was given, but
                    # only if it was defined already in the namespace.
                    if (action.default is not None and
                        isinstance(action.default, str) and
                        hasattr(namespace, action.dest) and
                        action.default is getattr(namespace, action.dest)):
                        setattr(namespace, action.dest,
                                self._get_value(action, action.default))

        if required_actions:
            actions_str = ', '.join(required_actions)
            self.error(
                f'The following arguments are required: {actions_str}')

        # Make sure all required groups had one option present.
        for group in self._mutually_exclusive_groups:
            if group.required:
                for action in group._group_actions:
                    if action in seen_non_default_actions:
                        break

                # If no actions were used, report the error.
                else:
                    names = [argparse._get_action_name(action)
                             for action in group._group_actions
                             if action.help is not argparse.SUPPRESS]
                    msg = 'One of the arguments %s is required'
                    self.error(msg % ' '.join(names))

        # Return the updated namespace and the extra arguments.
        return namespace, extras

    def add_argument(self, *args, **kwargs):
        """Define how a single command-line argument should be parsed.

        This wraps the standard method in order to support command completion.
        """
        completions = kwargs.pop('completions', [])
        get_completions = kwargs.pop('get_completions', None)
        action = super().add_argument(*args, **kwargs)
        self._completions[action.dest] = completions
        self._get_completions[action.dest] = get_completions
        return action

    def print_help(self, _file=None) -> None:
        """Display the help message."""
        self.popup = core.PopupNotification(
            self.format_help().splitlines(), 'Vpe_cmd_info',
            highlight='MessageWindow')

    def format_help(self):
        # pylint: disable=protected-access
        usage = self.usage
        if usage is not None:
            if self.parent is not None:
                usage = f'{self.parent.usage_prefix} {usage}'
        print("HI", usage)
        formatter = self._get_formatter()
        formatter.add_usage(
            usage, self._actions, self._mutually_exclusive_groups)
        formatter.add_text(self.description)

        # Any sub-command.
        subcommands = [
            (name, value[1]) for name, value in self.subcommands_table.items()]
        if subcommands:
            # There should only be one.
            undocumented = []
            documented = []
            for name, summary in subcommands:
                if summary:
                    documented.append((name, summary))
                else:
                    undocumented.append(name)
            formatter.start_section('subcommands')
            if undocumented:
                formatter.add_text(' '.join(undocumented))
            if documented:
                for name, summary in documented:
                    formatter.add_text(f'{name}: {summary}')
            formatter.end_section()

        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(
                [action for action in action_group._group_actions
                if not isinstance(action, SubcommandAction)])
            formatter.end_section()

        formatter.add_text(self.epilog)

        return formatter.format_help()

    def error(self, message):
        """Raise ArgumentError or print message and exit.

        This extends the standard method to prevent attempting to exit the
        program during argument parsing. If parsing is in progress, the message
        is used to raise an ArgumentError.
        """
        if self._parsing_in_progress and not self.exit_on_error:
            raise ArgumentError(str(message))
        super().error(message)

    def exit(self, status=0, message=None):
        """Raise ArgumentError and optionally print a message.

        This overrides the standard method to prevent attempting to exit the
        program during argument parsing.
        """
        if message:
            self._print_message(message, sys.stderr)
        raise ArgumentError(message)

    def get_completions(
            self, args: Sequence[str], at_new_arg: bool) -> list[str]:
        """Get the possible completions for a partial command.

        :args:       The list of arguments parsed so far.
        :at_new_arg: If false then create completions using args[-1] as the
                     starting point. Otherwise generate all possible values for
                     the next argument.
        :return:     A list of possible completion strings.
        """
        # Build up the list of all optional flags the first time this is
        # invoked.
        if self._all_optionals is None:
            self._all_optionals = []
            for action in self._actions:
                self._all_optionals.extend(action.option_strings)
            self._all_optionals.sort()

        if at_new_arg:
            partial = ''
        else:
            partial = args[-1]
            args = args[:-1]

        if partial.startswith('-'):
            if '=' not in partial:
                _, choices = unique_match(partial, self._all_optionals)
                return choices

        else:
            # Perform a partial parsing to select the correct sub-parser.
            try:
                _ = self.parse_known_args(args)
            except ArgumentError as e:
                msg = str(e)
                if msg.startswith('the following arguments are required: '):
                    _, _, names = msg.partition(':')
                    name = names.split(',')[0].strip()
                    get_completions = self._get_completions.get(name, None)
                    if get_completions is not None:
                        completions = get_completions(args)
                    else:
                        completions = self._completions.get(name, [])
                    _, choices = unique_match(partial, completions)
                    return choices

                return []

        return []


class SubcommandParser(ArgumentParser):
    """A ArgumentParser that uses a set of subcommands.

    This provides an alternative to using the add_subparsers method in the
    standard library's ArgumentParser. The results obtained are essentially the
    same, but with added support for command completion.
    """
    def __init__(
            self, command_name: str, subcommands_table: SubcommandsTable,
            *args, parent: ArgumentParser | None = None, **kwargs,
        ):
        print('New SubcommandParser', args, kwargs)
        super().__init__(
            command_name=command_name, parent=parent, *args, **kwargs)
        self.sub_parsers = {}
        self.add_argument(
            'subcommand', action=SubcommandAction,
            subcommands_table=subcommands_table)
        self.usage = f'{command_name} [options] subcommand'
        self.subcommands_table = subcommands_table

    @property
    def usage_prefix(self) -> str:
        """The prefix for usage messages."""
        if self.parent is not None:
            return f'{self.parent.usage_prefix} {self.prog}'
        else:
            return self.prog

    def add_parser(self, name, **kwargs):
        """Add an `ArgumentParser` for a subcommand.

        An ArgumentParser is created, with exit_on_error=False. You should not
        include exit_on_error in the keywrod argument of this method.

        :name:       The name of the subcommand.
        :kwargs:     The keyword arguments for the subcommand's ArgumentParser.
        :return:     The ArgumentParser for the subcommand.
        """
        assert name is not None
        self.sub_parsers[name] = ArgumentParser(
            command_name=name, parent=self, exit_on_error=False, **kwargs)
        return self.sub_parsers[name]

    def add_subcommand_parser(
            self, name: str, subcommands_table: SubcommandsTable, **kwargs):
        """Add a `SubcommandParser` for a subcommand.

        A SubcommandParser is created, with exit_on_error=False. You should
        not include exit_on_error in the keyword arguments of this method.

        :name:
            The name of the subcommand.
        :subcommands_table:
            The table of subcommands, which provides the names and summary.
        :kwargs:
            The keyword arguments for the subcommand's SubcommandParser.
        :return:
            The SubcommandParser for the subcommand.
        """
        assert name is not None
        self.sub_parsers[name] = SubcommandParser(
            command_name=name, subcommands_table=subcommands_table,
            parent=self, exit_on_error=False, **kwargs)
        return self.sub_parsers[name]

    def get_completions(self, args: Sequence[str], at_new_arg: bool):
        """Get the possible completions for a partial command.

        :args:       The list of arguments parsed so far.
        :at_new_arg: If false then create completions using args[-1] as the
                     starting point. Otherwise generate all possible values for
                     the next argument.
        :return:     A list of possible completion strings.
        """
        # If no arguments, the completions are all sub-commands.
        if not args:
            return sorted(self.sub_parsers)

        # Perform a partial parsing to select the correct sub-parser.
        arg_list = list(args)
        if arg_list and arg_list[-1] == '--':
            arg_list[-1] = '---'
        try:
            partial_args, rem_args = self.parse_known_args(arg_list)
            subcommand, choices = unique_match(
                partial_args.__subcommand__, self.sub_parsers)
            if rem_args and rem_args[-1] == '---':
                rem_args[-1] = '--'
        except ArgumentError as e:
            print("C-Error", e)
            return []

        # Provide sub-command completions only if at end of a partial
        # sub-command.
        if not at_new_arg and choices and not rem_args:
            return choices

        # Give up if the sub-command is not valid.
        if not subcommand:
            return []

        # Now we know which sub-command parser we are using.
        return self.sub_parsers[subcommand].get_completions(
            rem_args, at_new_arg)

    def parse_args(self, args: tuple[str]):
        """Parse the command arguments.

        Most of the work is done in parse_known_args, which converts arguments
        to actions, executing them as it goes. Most actions simply update this
        parser's `Namespace`, but a few (such as help) perform more complex
        actions.
        """
        try:
            args, rem_args = self.parse_known_args(args)
        except ArgumentError as e:
            core.error_msg(f'{e}', soon=True)
            return '', None
        except Stop:
            return '', None

        subcommand, choices = unique_match(
            args.__subcommand__, self.sub_parsers)
        if subcommand:
            return (
                subcommand, self.sub_parsers[subcommand].parse_args(rem_args))

        if not choices:
            raise ArgumentError(f'Unknown sub-command {args.subcommand!r}')
        raise ArgumentError(
            f'Ambiguous {self.prog} command; matches are: {" ".join(choices)}')


class CommandBase:
    """Base for a simple command or sub-command."""

    def __init__(
            self,
            parent_parser: argparse.SubcommandParser | None,
            name: str,
        ):
        self.name = name
        self.parent_parser = parent_parser
        self.arg_parser: argparse.ArgumentParser | None = self.create_parser()
        self.add_arguments()

    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for this command."""
        return self.parent_parser.add_parser(self.name)

    def add_arguments(self) -> None:
        """Add the arguments for this command."""

    def handle_command(self, args: Namespace) -> None:
        """Handle this command."""


class SubCommandBase(CommandBase):
    """Base for a command that has sub-commands."""

    sub_commands: ClassVar[dict[str, Type[SubCommandBase]]] = {}

    def __init__(
            self,
            parent_parser: argparse.SubcommandParser | None,
            name: str,
        ):
        super().__init__(parent_parser, name)
        self.sub_command_parser: argparse.SubcommandParser | None
        self.sub_command_parser = self.create_sub_command_parser()
        self.cmd_vector: dict[str, SubCommandBase] = {}
        self._init_sub_commands()

    def create_parser(self) -> None:
        """Create the argument parser for this command."""
        return None

    def create_sub_command_parser(self) -> argparse.SubcommandParser:
        """Create the sub-command argument parser for this command."""
        return self.parent_parser.add_subcommand_parser(
            self.name, self.sub_commands)

    def handle_sub_command(self, subcommand: str, args: Namespace):
        """Execute a specific sub-command."""
        if subcommand not in self.cmd_vector:
            error_msg('Invalid command')
            return

        handler = self.cmd_vector[subcommand]
        if isinstance(handler, SubCommandBase):
            handler.handle_sub_command(*args)
        if isinstance(handler, CommandBase):
            handler.handle_command(args)
        else:
            handler()

    def _init_sub_commands(self) -> None:
        """Recursively build sub-commands."""
        handler_spec: str | SubCommandBase
        for name, (handler_spec, _help_text) in self.sub_commands.items():
            if handler_spec == ':simple':
                self.cmd_vector[name] = getattr(self, f'handle_{name}')
                self.sub_command_parser.add_parser(name)
            else:
                self.cmd_vector[name] = handler_spec(
                    self.sub_command_parser, name)


class TopLevelSubCommandHandler(SubCommandBase):
    """Base for a top-level sub-command handler.

    This provides the main parser for a command that is composed of
    sub-commands.
    """
    registered_parsers: ClassVar[dict[str, SubcommandParser]] = {}
    parser: SubcommandParser

    def __init__(self, command_name: str):
        self.command_name = command_name
        super().__init__(parent_parser=None, name='')
        self._init_completion()
        core.define_command(
            command_name, self._handle_main_command,
            nargs='+',
            complete='customlist,VPE_Command_Complete',
            bar=True)

    def create_sub_command_parser(self) -> None:
        """Create the sub-command argument parser for this command."""
        parser = SubcommandParser(
            command_name=self.command_name,
            subcommands_table=self.sub_commands,
            exit_on_error=False)
        self.registered_parsers[self.command_name] = parser
        return parser

    def _handle_main_command(self, *cmd_args):
        """Parse and execute the main command."""
        sub_cmd, args = self.sub_command_parser.parse_args(cmd_args[1:])
        if sub_cmd == '':
            return
        self.handle_sub_command(sub_cmd, args)

    @classmethod
    def complete(cls) -> list[str]:
        """Attempt command line completion for a command.

        :return:
            A list strings representing the the possible completions.
        """
        try:
            vim_args = dict(getattr(wrappers.vim.vars, '_vpe_args_'))
            cmdline = vim_args['cmdline']
            pos = vim_args['cursorpos']

            left, _ = cmdline[:pos], cmdline[pos:]
            partial_command, _, left = left.partition(' ')
            args = left.split()
            at_new_arg = left.endswith(' ')
            command, _ = unique_match(partial_command, cls.registered_parsers)
            parser = cls.registered_parsers.get(command)
            if parser:
                return parser.get_completions(args, at_new_arg)
            else:
                return []

        # Possible exceptions are undefined, so we treat all exceptions as a
        # simple completion failure.
        except Exception as e:                   # pylint: disable=broad-except
            core.error_msg("Vpe command completion error:", e)
            print("Vpe command completion error:", e)

        return []

    def _init_completion(self) -> None:
        """Perform additional initialisation for completion support.

        This creates a Vim function the first time it is invoked. Subsequent
        calls do nothing.
        """
        if not wrappers.vim.exists('*VPE_Command_Complete'):
            print("Create completion (Vim) function")
            commands.py3('import vpe.vpe_commands')
            wrappers.vim.command(inspect.cleandoc("""
                function! VPE_Command_Complete(ArgLead, CmdLine, CursorPos)
                    let g:_vpe_args_ = {}
                    let g:_vpe_args_['cmdline'] = a:CmdLine
                    let g:_vpe_args_['cursorpos'] = a:CursorPos
                    let expr = 'vpe.vpe_commands.VPECommandProvider.complete()'
                    return py3eval(expr)
                endfunction
            """))


def unique_match(text, choices):
    """Find a unique match within `choices` that starts with `text`."""
    choices = sorted(choices)
    matches = [v for v in choices if v.startswith(text)]
    if matches and (matches[0] == text or len(matches) == 1):
        return matches[0], matches
    return '', matches
