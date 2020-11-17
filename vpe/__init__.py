"""Enhanced module for using Python3 in Vim.

This provides the Vim class, which is a wrapper around Vim's built-in *vim*
module. It is intended that a Vim instance can be uses as a replacement for the
*vim* module. For example:<py>:

    from vpe import vim
    # Now use 'vim' as an extended version of the *vim* module.
    # ...

This is compatible for versions of Vim from 8.0. It also needs Python 3.6 or
newer.

@vim:
    A replacement for (and wrapper around) the :vim:`python-vim` module.

    This is in instance of the `Vim` class.

@log:
    The Vpe log support object.

    This is an instance of the `Log` class.

The VPE module uses certain global Vim variables for its own internal purposes.
The names are chosen to be suitably obscure, but obviously associated with VPE.

_vpe_args_
    This is a dictionary that is used by a Vim function to pass information to
    Python callback functions. Predefined entries are:

        'uid'
            The unique ID for the callback function to be invoked.
        'args'
            A sequence of any unnamed arguments passed to the Vim function.
"""
# pylint: disable=too-many-lines

import pathlib
from typing import Tuple

import vim as _vim

# Make sure the 'common' and 'core' is are imported first. Later imports depend
# on it to some extent.
from .common import *
from .core import *
from .wrappers import vim, Vim

# pylint: disable=wrong-import-position
from . import channels                                                   # noqa
from . import mapping                                                    # noqa
from . import syntax                                                     # noqa
from .mapping import MapCallback  # noqa
from .wrappers import Buffer, Buffers, Current, GlobalOptions, TabPage   # noqa
from .wrappers import TabPages, Variables, Window, Windows, commands     # noqa
from .wrappers import Range, Struct, Registers                           # noqa

__api__ = [
    'AutoCmdGroup', 'Timer', 'Popup', 'PopupAtCursor', 'PopupBeval',
    'PopupNotification', 'PopupDialog', 'PopupMenu', 'VimError', 'Vim',
    'Registers', 'Log', 'error_msg', 'call_soon', 'vim', 'log',
    'saved_winview', 'highlight', 'pedit', 'popup_clear',
    'timer_stopall', 'find_buffer_by_name', 'script_py_path',
    'get_display_buffer', 'version', 'dot_vim_dir',

    'core', 'commands', 'mapping', 'syntax', 'wrappers',

    # Types and functions that should not be directly invoked.
    'Variables', 'Window', 'TabPage', 'Windows', 'TabPages', 'Buffers',
    'Current', 'GlobalOptions', 'Function', 'Buffer',
    'Range', 'Struct', 'ScratchBuffer',
]


def version() -> Tuple[int, int, int]:
    """The current VPE version as a 3 part tuple.

    The tuple follows the conventions of semantic versioning 2.0
    (https://semver.org/); *i.e.* (major, minor, patch).
    """
    return 0, 4, 0


def dot_vim_dir():
    """Return the path to the ~/.vim directory or its equivalent.

    :return:
        This returns the first directory in the runtimepath option.
    """
    return vim.options.runtimepath.split(',')[0]


def script_py_path() -> str:
    """Derive a python script name from the current Vim script name."""
    vim_script = pathlib.Path(vim.eval("expand('<sfile>')"))
    py_script = vim_script.parent / (vim_script.stem + '.py')
    return str(py_script)
