"""Enhanced module for using Python 3 in Vim.

This provides the Vim class, which is a wrapper around Vim's built-in *vim*
module. It is intended that a Vim instance can be uses as a replacement for the
*vim* module. For example:<py>:

    from vpe import vim
    # Now use 'vim' as an extended version of the *vim* module.
    # ...

@vim:
    A replacement for (and wrapper around) the :vim:`python-vim` module.

    This is in instance of the `Vim` class.

@log:
    The Vpe log support object.

    This is an instance of the `Log` class.

@commands:
    An object providing Vim commands as methods.

    This is an instance of the `Commands` class.

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
# ruff: noqa F403

# This should be imported by ~/.vim/plugin/000-vpe.vim, or something very
# similiar. This means that Vim has executed various non-gui ``...rc`` files.
# The ~/.vim/plugin/000-vpe.vim is named so that it is one of, if not the
# first, plugin to be loaded. This allows other plugins to fairly safely assume
# that VPE is is active. However, using the new VPE plug-in mechanism is a
# more robust approach.

import collections
import importlib
import importlib.machinery
import importlib.util
import io
import os
import sys
import traceback
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, Callable

import vim as _vim

# Add rich support if available.
from vpe import rich_support

# Make sure that 'common' and 'core' exported names are imported first. Later
# imports depend on this to some extent - which is why the imports are not in
# the order one would normally expect.
from vpe import common
from vpe.common import *
from vpe.core import *
from vpe.wrappers import Vim, vim

# pylint: disable=wrong-import-position
from vpe import (
    channels, mapping, message_bus, syntax, user_commands,
    vpe_commands as _vpe_commands)
from vpe.mapping import MapCallback
from vpe.wrappers import (
    BufListener, Buffer, Buffers, Current, GlobalOptions, Options, Range,
    Registers, Struct, TabPage, TabPages, VIM_DEFAULT, VI_DEFAULT, Variables,
    Window, Windows, commands)

__version__ = '0.7.0'

__api__ = [
    # Modules documented as part of the API.
    'app_ui_support',
    'channels',
    'commands',
    'config',
    'core',
    'diffs',
    'mapping',
    'message_bus',
    'panels',
    'syntax',
    'ui',
    'user_commands',
    'windows',
    'wrappers',

    # Other functions and classes exposed as part of the ``vpe`` namespace.
    'AutoCmdGroup',
    'BufListener',
    'Callback',
    'call_soon',
    'call_soon_once',
    'CommandInfo',
    'define_command',
    'dot_vim_dir',
    'echo_msg',
    'error_msg',
    'find_buffer_by_name',
    'Finish',
    'get_display_buffer',
    'get_managed_io_buffer',
    'highlight',
    'log',
    'Log',
    'OneShotTimer',
    'pedit',
    'Popup',
    'PopupAtCursor',
    'PopupBeval',
    'popup_clear',
    'PopupDialog',
    'PopupMenu',
    'PopupNotification',
    'Registers',
    'saved_current_window',
    'saved_winview',
    'script_py_path',
    'suppress_vim_invocation_errors',
    'temp_active_window',
    'Timer',
    'timer_stopall',
    'version',
    'vim',
    'Vim',
    'VimError',
    'warning_msg',

    # Types and functions that should not be directly invoked.
    'BufEventHandler',
    'Buffer',
    'Buffers',
    'CommandHandler',
    'Current',
    'EventHandler',
    'Function',
    'GlobalOptions',
    'Options',
    'ManagedIOBuffer',
    'Range',
    'ScratchBuffer',
    'Struct',
    'TabPage',
    'TabPages',
    'Variables',
    'VI_DEFAULT',
    'VIM_DEFAULT',
    'Window',
    'Windows',
]

PLUGIN_SUBDIR = 'vpe_plugins'

_plugin_hooks: dict[str, list[Callable[[], None]]] = {}


class Namespace:
    """Just an object that acts as an arbitrary namespace."""


# TODO: Discard this BEFORE release 1.0. It makes linting hard without
#       providing enough of an advantage; especially now I am transitioning to
#       ``pip`` installable plugins.
#: A place to store globally available information.
#:
#: Each plugin must choose a suitably unique name, e.g. 'zippy'. Then it can
#: store and retrieve arbitrary data as:<py>::
#:
#:    vpe.plugins['zippy'].unix_socket_name = 'unix:/tmp/zippy-sock'
#:
#: This is aimed at cross-plugin cooperation, but it can also make within
#: plugin code less coupled.
plugins: dict[str, object] = collections.defaultdict(Namespace)


class Finish(Exception):
    """Used by plugin's to abort installation.

    This is intended to play a similar role to the :vim:`:finish` command, as
    used in plug-ins that may not be able to complete initialisation.

    :reason: A string providing the reason for aborting.
    """
    def __init__(self, reason: str):
        # pylint: disable=useless-super-delegation
        super().__init__(reason)


def dot_vim_dir() -> str:
    """Provide the likely path to the ~/.vim directory or its equivalent.

    All this does is lookup $MYVIMDIR.
    """
    return os.environ.get('MYVIMDIR', '')


def script_py_path() -> str:
    """Derive a python script name from the current Vim script name."""
    vim_script = Path(vim.eval("expand('<sfile>')"))
    py_script = vim_script.parent / (vim_script.stem + '.py')
    return str(py_script)


def add_post_plugin_hook(name: str, func: Callable):
    """Add a function to be called after a VPE plugin has been installed.

    This is currently intended for internal use.

    :name: The name of the VPE plugin.
    :func: The function to be invoked.
    """
    _plugin_hooks.setdefault(name, [])
    _plugin_hooks.setdefault(name).append(func)


def _is_plugin(path):
    """Test whether a pythonfile is a plugin.

    :path: The Path for the python file.
    """
    with open(path, encoding='utf-8') as f:
        line = f.readline()
    return line.startswith('"""VPE-plugin: ')


def _import_possible_plugin(path):
    """Import a possible plugin.

    :path: The Path for the plugin. This may be a python file or a package
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

    if os.environ.get('VPE_TEST_MODE', None):
        # We are running tests and only want to install test specific plugins.
        if not path.name.startswith('vpe_test_only_'):
            return                                           # pragma: no cover

    try:
        # pylint: disable=exec-used
        plugin_name = f'{PLUGIN_SUBDIR}.{path.stem}'
        exec(f'import {plugin_name}')
    except Finish as exc:
        print('Could not initialise VPE plug-in {path}')
        print(f'   {exc}')
        return
    except Exception:                            # pylint: disable=broad-except
        traceback.print_exc()
        print(f'Error loading VPE plug-in {path}')
        return

    # Run any user provided post-plugin hook function.
    funcs = _plugin_hooks.get(path.stem, [])
    for func in funcs:
        try:
            func()
        except Exception as e:                   # pylint: disable=broad-except
            if not os.environ.get('VPE_TEST_MODE', None):    # pragma: no cover
                error_msg(f'Error in post-plugin hook {func}, {e}', soon=True)


def _load_plugins(old_plugins_only: bool = False):
    """Load any VPE based plugins."""

    plugin_dir = Path(dot_vim_dir()) / f'pack/{PLUGIN_SUBDIR}'
    if plugin_dir.is_dir():
        possible_plugins = [
            p for p in plugin_dir.glob('*') if p.suffix in ('.py', '')]
        possible_plugins = [
            p for p in possible_plugins if not p.name.startswith('_')]
        possible_plugins = [p for p in possible_plugins if '-' not in p.name]
        for p in sorted(possible_plugins):
            _import_possible_plugin(p)
        plugin_doc_dir = plugin_dir / 'doc'
        if plugin_doc_dir.exists():
            vim.options.runtimepath += str(plugin_dir)

    if not old_plugins_only:
        _load_new_plugins()                                  # pragma: no cover


def _load_new_plugins():
    # pragma: no cover
    discovered_plugins = entry_points(group='vpe.plugins')
    for entry_point in discovered_plugins:
        # TODO: Need to handle plugin errors gracefully.
        try:
            module = entry_point.load()
        except Exception as e:
            f = io.StringIO()
            traceback.print_exc(file=f)
            print(
                f'Error loading plugin {entry_point.name}: {e}'
                f' \n{f.getvalue()}')
            call_soon(print, f.getvalue())
            continue

        print(f'New plugin: {entry_point.name}')
        try:
            init_func = getattr(module, 'init')
        except AttributeError:
            pass
        else:
            if callable(init_func):
                common.call_soon(print, f'Set up init for {entry_point.name}')
                common.call_soon(init_func)


def _init_vpe_plugins(old_plugins_only: bool = False):
    """Initialise the VPE plug-in infrastructure.

    This only does anything if the directory .vim/pack/vpe_plugins (or
    Windows equivalent) exists. In which case:

    1. A package is created that maps onto the vpe_plugins directory.
    2. If one does not already exist, an __init__.py is created in the
       vpe_plugins directory
    """
    plugin_dir = Path(dot_vim_dir()) / f'pack/{PLUGIN_SUBDIR}'

    if plugin_dir.is_dir():

        spec = importlib.machinery.ModuleSpec('vpe_plugins', None, is_package=True)
        package = importlib.util.module_from_spec(spec)
        package.__path__.append(str(plugin_dir))
        sys.modules[PLUGIN_SUBDIR] = package

        init_path = plugin_dir / '__init__.py'
        if not init_path.exists():
            init_path.write_text('')

    _load_plugins(old_plugins_only=old_plugins_only)


class temp_log:                                              # pragma: no cover
    """Temporarily append output to a log file.

    This is only intended to be used for ad-hoc debugging.
    """
    f: Any
    saved: tuple[Any, Any]

    def __init__(self, file_path: Path | str):
        self.path = Path(file_path)

    def __enter__(self):
        self.f = open(self.path, 'at', encoding='utf-8')
        self.saved = sys.stderr, sys.stdout
        sys.stderr = sys.stdout = self.f

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.f.close()
        sys.stderr, sys.stdout = self.saved


def post_init(old_plugins_only: bool = False):
    """Perform post-initialisation.

    This is invoked by $HOME/.vim/plugin/000-vpe.vim immediately after the
    `vpe` package is imported.

    :old_plugins_only:
        This is just for testing.
    """
    _vpe_commands.init()
    _init_vpe_plugins(old_plugins_only=old_plugins_only)
