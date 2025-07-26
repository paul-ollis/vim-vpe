"""Provider of VPE support commands.

This module provied the Vpe command, which itself provides a number of
sub-commands.

A summary of the commands::

    Vpe log show | hide
    Vpe log length [max_length]
    Vpe log redirect [on | off]
    Vpe insert_control_vars
"""
from __future__ import annotations

from functools import partial
from inspect import cleandoc
from typing import TYPE_CHECKING

from vpe import core, vim
from vpe.argparse import CommandBase, SubCommandBase, TopLevelSubCommandHandler

if TYPE_CHECKING:
    from argparse import Namespace
    from argparse import Namespace

# Function to print error messages.
error_msg = partial(core.error_msg, soon=True)

# Function to print informational messages.
echo_msg = partial(core.echo_msg, soon=True)


class LogLengthCommand(CommandBase):
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


class LogRedirectCommand(CommandBase):
    """The 'log redirect' sub-command support."""

    def add_arguments(self) -> None:
        """Add the arguments for this command."""
        self.parser.add_argument(
            'flag', choices=('on', 'off'), nargs='?',
            help='Redirect to the log "on" or "off".')

    def handle_command(self, args: Namespace):
        """Handle the 'Vpe log redirect' command."""
        if args.flag is not None:
            if args.flag == 'on':
                core.log.redirect()
            else:
                core.log.unredirect()
        if core.log.saved_out:
            echo_msg('Stdout/stderr being redirected to the log')
        else:
            echo_msg('Stdout/stderr not being redirected to the log')


class LogSubCommand(SubCommandBase):
    """The 'log' sub-command support."""

    sub_commands = {
        'show': (':simple', 'Show the log file buffer.'),
        'hide': (':simple', 'Hide the log file buffer.'),
        'length': (LogLengthCommand, 'Display/set the log file max length'),
        'redirect': (
            LogRedirectCommand, 'Display/set stdout/sterr redirection'),
    }

    def handle_show(self) -> None:
        """Handle the 'Vpe log show' command."""
        core.log.show()

    def handle_hide(self) -> None:
        """Handle the 'Vpe log hide' command."""
        core.log.hide()


class VPECommandProvider(TopLevelSubCommandHandler):
    """A class to provide some VPE support commands."""

    sub_commands = {
        'log': (LogSubCommand, 'Log file management.'),
        'insert_control_vars': (':simple', "Insert VPE's control variables"),
    }

    def handle_insert_control_vars(self) -> None:
        """Execute the 'Vpe insert_control_vars' command."""
        vpe_vars = (
            (
                'vpe_do_not_auto_import',
                """Prevent any of the imports/namespace insertions. This is
                equivalent to setting all the below variable to a true
                value.""",
            ),
            (
                'vpe_do_not_auto_import_vpe',
                '''Prevent `vpe` being imported into Vim's python
                namespace.''',
            ),
            (
                'vpe_do_not_auto_import_vim',
                '''Prevent `vim` (the `Vim` singleton) being imported into
                Vim's python namespace.''',
            ),
            (
                'vpe_do_not_auto_import_vpe_into_builtins',
                '''Prevent `vpe` being imported into Pythons's builtins
                namespace.''',
            ),
            (
                'vpe_do_not_auto_import_vim_into_builtins',
                '''Prevent `vim` (the `Vim` singleton) being imported into
                Python's builtins namespace.''',
            ),
        )
        buf = vim.current.buffer
        is_vim9 = 'vim9script' in [s.strip() for s in buf[:10]]
        row, _ = vim.current.window.cursor
        lines = []
        for i, (name, description) in enumerate(vpe_vars):
            description = cleandoc(description)
            if i:
                lines.append('')
            for line in description.splitlines():
                if is_vim9:
                    lines.append(f'# {line}')
                else:
                    lines.append(f'" {line}')
            if is_vim9:
                lines.append(f'g:{name} = 0')
            else:
                lines.append(f'let g:{name} = 0')
        buf[row-1:row-1] = lines


def init():
    """Initialise the VPE commands."""
    global _vpe_commands                     # pylint: disable=global-statement

    _vpe_commands = VPECommandProvider('Vpe')


# Create the VPE command provider.
_vpe_commands: VPECommandProvider | None = None
