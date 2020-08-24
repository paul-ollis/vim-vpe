"""Enhanced module for using Python3 in Vim.

This provides the Vim class, which is a wrapper around Vim's built-in *vim*
module. It is intended that a Vim instance can be uses as a replacement for the
*vim* module. For example:<py>:

    from vpe import vim
    # Now use 'vim' as an extended version of the *vim* module.
    # ...

This was developed for Vim version 8.1. It will probably work for Vim 8.0, but
is very unlikely to be compatible with earlier versions. I plan that future
versions of *vpe* will be backwardly compatible with version 8.1.

@vim:
    A replacement for (and wrapper around) the :vim:`python-vim` module.

    This is in instance of the `Vim` class.

@log:
    The Vpe log support object.

    This is an instance of the `Log` class.
"""
# pylint: disable=too-many-lines

import pathlib

import vim as _vim

# Make sure the 'common' and 'core' is are imported first. Later imports depend
# on it to some extent.
from .common import *
from .core import *
from .wrappers import vim, Vim

# TODO: Clean up elaboration order mess.
RET_VAR = 'g:VPE_ret_value'
vim.vars[RET_VAR] = ''

# pylint: disable=wrong-import-position
from .channels import Channel  # noqa
from . import commands  # noqa
from . import mapping  # noqa
from . import syntax  # noqa
from .mapping import MapCallback  # noqa
from .wrappers import Buffer, Buffers, Current, GlobalOptions, TabPage   # noqa
from .wrappers import TabPages, Variables, Window, Windows               # noqa

__api__ = [
    'AutoCmdGroup', 'Timer', 'Popup', 'PopupAtCursor', 'PopupBeval',
    'PopupNotification', 'PopupDialog', 'PopupMenu', 'VimError', 'Vim',
    'Registers', 'Log', 'error_msg', 'call_soon', 'vim', 'log',
    'saved_winview', 'highlight', 'pedit', 'popup_clear',
    'timer_stopall', 'find_buffer_by_name', 'script_py_path', 'Channel',
    'get_display_buffer',

    'core', 'commands', 'mapping', 'syntax', 'wrappers',

    # Types and functions that should not be directly invoked.
    'Variables', 'Window', 'TabPage', 'Windows', 'TabPages', 'Buffers',
    'Current', 'GlobalOptions', 'Function',
]


def script_py_path() -> str:
    """Derive a python script name from the current Vim script name."""
    vim_script = pathlib.Path(vim.eval("expand('<sfile>')"))
    py_script = vim_script.parent / (vim_script.stem + '.py')
    return str(py_script)
