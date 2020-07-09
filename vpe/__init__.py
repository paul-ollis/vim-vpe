"""Enhanced module for using Python3 in Vim.

This provides the Vim class, which is a wrapper around Vim's built-in *vim*
module. It is intended that a Vim instance can be uses as a replacement for the
*vim* module. For example:

    import vpe
    vim = vpe.Vim()
    # Now use 'vim' as an extended version of the *vim* module.
    # ...

Note that ``vpe.Vim()`` always returns the same (singleton) instance.

This was developed for Vim version 8.1. It will probably work for Vim 8.0, but
is very unlikely to be compatible with earlier versions. I plan that future
versions of *vpe* will be backwardly compatible with version 8.1.
"""

import contextlib
import itertools
import pathlib
import sys

import vim as _vim

from . import buffers
from . import commands
from . import current
from . import dictionaries
from . import options
from . import tabpages
from . import variables
from . import windows

_wrappers = {
    type(_vim.options): options.Options,
    _vim.Buffer: buffers.Buffer,
    _vim.Dictionary:    dictionaries.Dictionary,
    _vim.Range: buffers.Range,
    _vim.TabPage: tabpages.TabPage,
    _vim.Window: windows.Window,
}
_blockedVimFunctions = set((
    "libcall",
    "libcallnr",
))
_vim_singletons = {
    'buffers': buffers.buffers,
    'current': current.current,
    'options': options.global_options,
    'tabpages': tabpages.tabpages,
    'vars': variables.vars,
    'vvars': variables.vvars,
    'windows': windows.windows,
}

_routed_functions = {}
_func_id_source = itertools.count()


def wrap_item(item):
    wrapper = _wrappers.get(type(item), None)
    if wrapper is not None:
        return wrapper(item)
    elif isinstance(item, bytes):
        return item.decode()
    return item


class Timer:
    _timers = {}

    def __init__(self, ms, func, kwargs):
        vim_func, self._func_uid = _routed_function(self._on_timer)
        self._id = vim.timer_start(ms, vim_func, kwargs)
        self._timers[self._id] = self
        self.callback = func

    @property
    def id(self):
        return self._id

    @property
    def time(self):
        return self._get_info('time')

    @property
    def repeat(self):
        return self._get_info('repeat')

    @property
    def remaining(self):
        return self._get_info('remaining')

    @property
    def paused(self):
        return bool(self._get_info('paused'))

    def _get_info(self, name):
        info = vim.timer_info(self.id)
        if info:
            return info[0][name]
        
    def stop(self):
        vim.timer_stop(self.id)
        self._cleanup()

    def pause(self):
        vim.timer_pause(self.id, True)

    def resume(self):
        vim.timer_pause(self.id, False)

    def _invoke_self(self):
        if self.repeat == 1:
            self._cleanup()
        self.callback(self)

    def _cleanup(self):
        _routed_functions.pop(self._func_uid, None)
        self._timers.pop(self.id, None)

    @classmethod
    def stop_all(cls):
        vim.timer_stopall()
        for timer in list(cls._timers.values()):
            timer._cleanup()
        
    @classmethod
    def _on_timer(cls, tid):
        """The callback for all active timers.

        This performs routing to the actual Timer instamce.
        """
        timer = cls._timers.get(tid, None)
        if timer is not None:
            timer._invoke_self()


class PopupWindow:
    _popups = {}

    def __init__(self, func, content, kwargs):
        self._filter_callback = kwargs.get('filter', None)
        self._close_callback = kwargs.get('callback', None)
        if self._filter_callback:
            vim_func, self._filter_uid = _routed_function(self._on_filter)
            kwargs['filter'] = vim_func
        else:
            self._filter_uid = None
        vim_func, self._close_uid = _routed_function(self._on_close)
        kwargs['callback'] = vim_func
        self._id = func(content, kwargs)
        self._popups[self._id] = self

    @property
    def id(self):
        return self._id

    def _cleanup(self):
        _routed_functions.pop(self._filter_uid, None)
        _routed_functions.pop(self._close_uid, None)
        self._popups.pop(self._id, None)

    @classmethod
    def _on_close(cls, id, close_arg):
        popup = cls._popups.get(id, None)
        if popup is not None:
            if popup._close_callback:
                popup._close_callback(id, close_arg)
            popup._cleanup()

    @classmethod
    def _on_filter(cls, id, key_str):
        popup = cls._popups.get(id, None)
        if popup is not None:
            return popup._filter_callback(id, key_str)


class Function(_vim.Function):
    """Wrapper around a vim.Function.

    This provides some minimal cooercion of function return types.

    - A vim.Dictionary is wrapped as a VPE Dictionary.
    - A bytes instance is decodes to a string.
    """

    def __call__ (self, *args, **kwargs):
        v = super().__call__(*args, **kwargs)
        if isinstance(v, _vim.Dictionary):
            return dictionaries.Dictionary(v)
        elif isinstance(v, bytes):
            return v.decode()
        return v


class Registers:
    """Pythonic access to the Vim registers."""

    def __getitem__(self, reg_name):
        """Allow reading registers as dictionary entries.

        The reg_name may also be an integer value in the range 0-9.
        """
        return _vim.eval(f'@{reg_name}')

    def __setitem__(self, reg_name, value):
        """Allow setting registers as dictionary entries.

        The reg_name may also be an integer value in the range 0-9.
        """
        return vim.setreg(f'{reg_name}', value)


class _VimDirectFunctions:
    """Transparent access to Vim's functions."""

    def __getattr__(self, name):
        fname_form = f'*{name}'
        if _vim.eval(f'exists({fname_form!r})') != '0':
            if name not in _blockedVimFunctions:
                return Function(name)

        raise AttributeError(
            f'{self.__class__.__name__} object has no attribute {name!r}')


class _VimOverrides:
    """Overrides of the basic *vim* API."""

    def __getattr__(self, name):
        """For non-overridden attributes use the vim module's official API."""
        if name in _vim_singletons:
            return _vim_singletons[name]
        try:
            attr = getattr(_vim, name)
        except AttributeError:
            return super().__getattr__(name)
        else:
            return wrap_item(attr)

    def __setattr__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value
        else:
            raise AttributeError(
                f'can\'t set attribute {name} for {self.__class__.__name__}')


class Vim(
        _VimOverrides,
        _VimDirectFunctions,
    ):
    """A wrapper around and replacement for the *vim* module."""
    _registers = Registers()

    def __new__(cls, *args, **kwargs):
        """Ensure only a single Vim instance ever exists."""
        try:
            cls._myself
        except AttributeError:
            cls._myself = super().__new__(cls, *args, **kwargs)
        return cls._myself

    def temp_options(self, **presets):
        """Context used to temporarily change options."""
        return proxies.TemporaryOptions(self.options, **presets)

    @property
    def registers(self):
        return self._registers

    def vim(self):
        """Get the underlying built-in vim module."""
        return _vim


def script_py_path():
    vim = Vim()
    vim_script = pathlib.Path(vim.eval("expand('<sfile>')"))
    py_script = vim_script.parent / (vim_script.stem + '.py')
    return str(py_script)

    
def highlight(
        *, group=None, clear=False, default=False, link=None, disable=False,
        **kwargs):
    """Python version of the highlight command.

    This provides keyword arguments for all the command parameters. These are
    generally taken from the |:highlight| command's documentation.

    :group:
        The name of the group being defined. If omitted then all other
        arguments except *clear* are ignored.

    :clear:
        If set then the command ``highlight clear [<group>]`` is generated. All
        other arguments are ignored.

    :disable:
        If set then the specified *group* is disabled using the command:

            ``highlight <group> NONE``

    :link:
        If set then a link command will be generated of the form:

            ``highlight link <group> <link>``.

        Other arguments are ignored.

    :default:
        If set then the generated command has the form ``highlight default...``.

    :kwargs:
        The remain keyword arguments act like the |:highlight| command's
        keyword arguments.
    """
    args = []
    if link:
        args.append('link')
        args.append(group)
        args.append(link)
        return commands.highlight(*args)
    if group:
        args.append(group)
    if clear:
        args[:] = ['clear']
        return commands.highlight(*args)

    if disable:
        args.append('NONE')
        return commands.highlight(*args)

    if default:
        args.append('default')

    for name, value in kwargs.items():
        args.append(f'{name}={value}')

    return commands.highlight(*args)


def error(*args):
    """A print-like function that writes an error message.

    Unlike using sys.stderr directly, this does not raise a vim.error.
    """
    msg = ' '.join(str(a) for a in args)
    _vim.command(f'echohl ErrorMsg')
    _vim.command(f'echomsg {msg!r}')


def pedit(path, silent=True, noerrors=False):
    cmd = []
    if silent or noerrors:
        if noerrors:
            cmd.append('silent!')
        else:
            cmd.append('silent')
    cmd.extend(['pedit', path])
    _vim.command(' '.join(cmd))


def _routed_function(func):
    uid = str(next(_func_id_source))
    vim_func = _vim.Function('VPE_py_call', args=[uid])
    _routed_functions[uid] = func
    return vim_func, uid


def dispatch(ident, *args):
    vim.vars.VPE_ret = ''
    func = _routed_functions.get(ident.decode(), None)
    if func is None:
        print(f'No function for {ident}')
        return
    vim.vars.VPE_ret = func(*args) 


def _admin_status():
    print(f'{len(Timer._timers)=}')
    print(f'{len(PopupWindow._popups)=}')
    print(f'{len(_routed_functions)=}')


def timer_start(ms, func, **kwargs):
    """Wrapping of vim.timer_start.

    :param ms:
        The timer period/interval in milliseconds.
    :param func:
        A Python callable. It should accept a single *timer* argument, which
        will be a Timer instance.
    :kwargs:
        Remaining keyword arguments provide the options to the underlying
        vim.timer_start call.

    :return:
        A Timer instance that can be used to query and control underlying Vim
        timer.
    """
    return Timer(ms, func, kwargs)


def call_soon(func):
    def do_call(timer):
        func()
    timer_start(0, do_call)


def timer_stopall():
    Timer.stop_all()


def play():
    def _on_close(wid, close_arg):
        print(f'Def done! {wid=} {close_arg=}')

    def _on_key(wid, key_str):
        vim.popup_close(wid)

    popup_atcursor(['Hi', 'Paul'], callback=_on_close, filter=_on_key)


def popup_notification(content, **kwargs):
    """Invoke vim.popup_notification with kwargs as options."""
    return PopupWindow(vim.popup_notification, content, kwargs)


def popup_create(content, **kwargs):
    """Invoke vim.popup_create with kwargs as options."""
    return PopupWindow(vim.popup_create, content, kwargs)


def popup_atcursor(content, **kwargs):
    """Invoke vim.popup_atcursor with kwargs as options."""
    return PopupWindow(vim.popup_atcursor, content, kwargs)


def popup_beval(content, **kwargs):
    """Invoke vim.popup_beval with kwargs as options."""
    return PopupWindow(vim.popup_beval, content, kwargs)


def popup_dialog(content, **kwargs):
    """Invoke vim.popup_dialog with kwargs as options."""
    return PopupWindow(vim.popup_dialog, content, kwargs)


def popup_menu(content, **kwargs):
    """Invoke vim.popup_menu with kwargs as options."""
    return PopupWindow(vim.popup_menu, content, kwargs)


# Create a Vim instance for module use.
vim = Vim()
