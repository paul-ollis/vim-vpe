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

@commands:
    An object providing Vim commands a methods.

    This is in instance of the `Commands` class.

@VI_DEFAULT:  Special value representing default Vi value for an option.
@VIM_DEFAULT: Special value representing default Vim value for an option.

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

import importlib
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Tuple, Union

import vim as _vim

# Make sure the 'common' and 'core' is are imported first. Later imports depend
# on it to some extent.
from .common import *
from .core import *
from .wrappers import Vim, vim

# pylint: disable=wrong-import-position
from . import channels, mapping, syntax
from .mapping import MapCallback
from .wrappers import (
    Buffer, Buffers, Current, GlobalOptions, Range, Registers, Struct, TabPage,
    TabPages, VIM_DEFAULT, VI_DEFAULT, Variables, Window, Windows, commands)

__api__ = [
    'AutoCmdGroup', 'Timer', 'Popup', 'PopupAtCursor', 'PopupBeval',
    'PopupNotification', 'PopupDialog', 'PopupMenu', 'VimError', 'Vim',
    'Registers', 'Log', 'echo_msg', 'error_msg', 'warning_msg', 'call_soon',
    'vim', 'log', 'saved_winview', 'highlight', 'pedit', 'popup_clear',
    'timer_stopall', 'find_buffer_by_name', 'script_py_path',
    'get_display_buffer', 'version', 'dot_vim_dir', 'temp_active_window',
    'define_command', 'CommandInfo',

    'core', 'commands', 'mapping', 'syntax', 'wrappers',

    # Types and functions that should not be directly invoked.
    'Variables', 'Window', 'TabPage', 'Windows', 'TabPages', 'Buffers',
    'Current', 'GlobalOptions', 'Function', 'Buffer',
    'Range', 'Struct', 'ScratchBuffer', 'VI_DEFAULT', 'VIM_DEFAULT',
    'CommandHandler', 'EventHandler', 'BufEventHandler',
]

PLUGIN_SUBDIR = 'vpe_plugins'

_plugin_hooks = {}


class Finish(Exception):
    """Used by plugin's to abort installation.

    This is intended to play the same role as the :vim:`:finish` command as
    used in plug-ins that may not be able to complete initialisation.
    """


def version() -> Tuple[int, int, int]:
    """The current VPE version as a 3 part tuple.

    The tuple follows the conventions of semantic versioning 2.0
    (https://semver.org/); *i.e.* (major, minor, patch).
    """
    return 0, 5, 0


def dot_vim_dir() -> str:
    """Return the path to the ~/.vim directory or its equivalent.

    :return:
        This returns the first directory in the runtimepath option.
    """
    return vim.options.runtimepath.split(',')[0]


def script_py_path() -> str:
    """Derive a python script name from the current Vim script name."""
    vim_script = Path(vim.eval("expand('<sfile>')"))
    py_script = vim_script.parent / (vim_script.stem + '.py')
    return str(py_script)


def add_post_plugin_hook(name: str, func: Callable):
    """Add a function to be called after a VPE plugin has been installed.

    :name: The name of the VPE plugin.
    :func: The function to be invoked.
    """
    _plugin_hooks.setdefault(name, [])
    _plugin_hooks.setdefault(name).append(func)


def _is_plugin(path):
    """Test whether a pythonfile is a plugin.

    :path: The Path for the python file.
    """
    with open(path) as f:
        line = f.readline()
    return line.startswith('"""VPE-plugin: ')


def _import_possible_plugin(path):
    """Import a possible plugin.

    :path: The Path for the plugin. This may be a pyton file or a package
           directory.
    """
    if path.is_dir():
        init = path / '__init__.py'
        if not init.exists():
            return
        if not _is_plugin(init):
            return
    else:
        if not _is_plugin(path):
            return
    try:
        exec(f'import {PLUGIN_SUBDIR}.{path.stem}')
    except Finish as exc:
        print('Could not initialise VPE plug-in {path}')
        print('   {exc}')
        return
    except Exception as exc:
        traceback.print_exc()
        print(f'Error loading VPE plug-in {path}')
        return

    # Run any user provided post-plugin hook function.
    funcs = _plugin_hooks.get(path.stem, [])
    for func in funcs:
        try:
            func()
        except Exception as e:
            core.error_msg(f'Error in post-plugin hook {func}, {e}', soon=True)


def _load_plugins():
    """Load any VPE based plugins."""
    plugin_dir = Path(dot_vim_dir()) / f'pack/{PLUGIN_SUBDIR}'
    possible_plugins = [
        p for p in plugin_dir.glob('*') if p.suffix in ('.py', '')]
    possible_plugins = [
        p for p in possible_plugins if not p.name.startswith('_')]
    for p in sorted(possible_plugins):
        _import_possible_plugin(p)


def _init_vpe_plugins():
    """Initialise the VPE plug-in infrastructure.

    This only does anything if the directory .vim/pack/vpe_plugins (or
    Windows equivalent) exists. In which case:

    1. A package is created that maps onto the vpe_plugins directory.
    2. If one does not already exist, an __init__.py is created in the
       vpe_plugins directory
    """
    plugin_dir = Path(dot_vim_dir()) / f'pack/{PLUGIN_SUBDIR}'
    if not plugin_dir.is_dir():
        return

    spec = importlib.machinery.ModuleSpec('vpe_plugins', None, is_package=True)
    package = importlib.util.module_from_spec(spec)
    package.__path__.append(str(plugin_dir))
    sys.modules[PLUGIN_SUBDIR] = package

    init_path = plugin_dir / '__init__.py'
    if not init_path.exists():
        init_path.write_text('')

    if vim.vvars.vim_did_enter:
        _load_plugins()
    else:                                                    # pragma: no cover
         with AutoCmdGroup('VPECore') as au:
             au.add('VimEnter', _load_plugins, nested=True)


class temp_log:                                              # pragma: no cover
    """Temporarily append output to a log file.

    This is only intended to be used for ad-hoc debugging.
    """
    f: Any
    saved: Tuple[Any, Any]

    def __init__(self, file_path: Union[Path, str]):
        self.path = Path(file_path)

    def __enter__(self):
        self.f = open(self.path, 'at')
        self.saved = sys.stderr, sys.stdout
        sys.stderr = sys.stdout = self.f

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.f.close()
        sys.stderr, sys.stdout = self.saved


_init_vpe_plugins()
del _init_vpe_plugins
