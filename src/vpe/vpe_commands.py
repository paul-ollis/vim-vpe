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

import vpe
from vpe import core, vim
from vpe.user_commands import (
    CommandHandler, SubcommandHandlerBase, TopLevelSubcommandHandler)

if TYPE_CHECKING:
    from argparse import Namespace

# Function to print error messages.
error_msg = partial(core.error_msg, soon=True)

# Function to print informational messages.
echo_msg = partial(core.echo_msg, soon=True)


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


class LogRedirectCommand(CommandHandler):
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


class LogSubCommand(SubcommandHandlerBase):
    """The 'log' sub-command support."""

    subcommands = {
        'show': (':simple', 'Show the log file buffer.'),
        'hide': (':simple', 'Hide the log file buffer.'),
        'clear': (':simple', 'lear the log contents.'),
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

    def handle_clear(self, _args: Namespace) -> None:
        """Handle the 'Vpe log clear' command."""
        core.log.clear()


class VPECommandProvider(TopLevelSubcommandHandler):
    """A class to provide some VPE support commands."""

    subcommands = {
        'log': (LogSubCommand, 'Log file management.'),
        'insert_config': (':simple', 'Insert the vpe_config global variable.'),
        'install': (':simple', 'Install Vim plugin and help files.'),
        'version': (':simple', 'Display the VPE version number.'),
    }
    range = True

    def handle_insert_config(self, _args: Namespace) -> None:
        """Execute the 'Vpe insert_config' command."""
        vpe_vars = (
            (
                'import.vpe',
                '''Import `vpe` imported into Vim's python namespace.''',
            ),
            (
                'import.vim',
                '''Import `vim` (the `Vim` singleton) into Vim's python
                namespace.''',
            ),
            (
                'import.vpe_into_builtins',
                '''Import `vpe` into Pythons's builtins namespace.''',
            ),
            (
                'import.vim_into_builtins',
                '''Import `vim` (the `Vim` singleton) into Python's builtins
                namespace.''',
            ),
        )
        buf = vim.current.buffer
        is_vim9 = 'vim9script' in [s.strip() for s in buf[:10]]
        row, _ = vim.current.window.cursor
        lines = []
        if is_vim9:
            lines.append('# The VPE configuration structure.')
            lines.append('var g:vpe_config = {}')
            lines.append('g:vpe_config.import = {}')
        else:
            lines.append('" The VPE configuration structure.')
            lines.append('let g:vpe_config = {}')
            lines.append('let g:vpe_config.import = {}')
        for name, description in vpe_vars:
            description = cleandoc(description)
            lines.append('')
            for line in description.splitlines():
                if is_vim9:
                    lines.append(f'# {line}')
                else:
                    lines.append(f'" {line}')
            if is_vim9:
                lines.append(f'g:vpe_config.{name} = 1')
            else:
                lines.append(f'let g:vpe_config.{name} = 1')
        buf[row-1:row-1] = lines

    def handle_install(self, _args: Namespace) -> None:
        """Execute the 'Vpe install' command."""
        # pylint: disable=import-outside-toplevel
        import vpe.install as vpe_install

        vpe_install.run()
        vpe.commands.messages()

    def handle_version(self, _args: Namespace) -> None:
        """Execute the 'Vpe version' command."""
        echo_msg(f'VPE version {vpe.__version__}')


def init():
    """Initialise the VPE commands."""
    global _vpe_commands                     # pylint: disable=global-statement

    _vpe_commands = VPECommandProvider('Vpe')


# Create the VPE command provider.
_vpe_commands: VPECommandProvider | None = None
