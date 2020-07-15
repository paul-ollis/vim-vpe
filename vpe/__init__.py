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

import collections
import contextlib
import functools
import itertools
import pathlib
import sys
import weakref

import vim as _vim

from . import buffers
from . import colors
from . import commands
from . import current
from . import dictionaries
from . import options
from . import tabpages
from . import variables
from . import windows

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

# TODO: Rationalise routed functions and Callbacks.
_routed_functions = {}
_func_id_source = itertools.count()
id_source = itertools.count()

_vim.command('let g:_vpe_example_list_ = []')
_vim.command('let g:_vpe_example_dict_ = {}')
_vim_list_type = _vim.vars['_vpe_example_list_'].__class__
_vim_dict_type = _vim.vars['_vpe_example_dict_'].__class__
_vim.command('unlet g:_vpe_example_list_ g:_vpe_example_dict_')

_std_vim_colours = set((
    "Black", "DarkBlue", "DarkGreen", "DarkCyan",
    "DarkRed", "DarkMagenta", "Brown", "DarkYellow",
    "Gray", "Grey", "LightGray", "LightGrey",
    "DarkGray", "DarkGrey",
    "Blue", "LightBlue", "Green", "LightGreen",
    "Cyan", "LightCyan", "Red", "LightRed", "Magenta",
    "LightMagenta", "Yellow", "LightYellow", "White", "NONE"))


def _get_wrapped_buffer(vim_buffer):
    b = buffers.Buffer.get_known(vim_buffer)
    if b is None:
        b = buffers.Buffer(vim_buffer)
    return b
    

class _Struct:
    pass


# TODO: Very similar to the other Scratch buffer in py_core.
class Scratch(buffers.Buffer):
    """A scratch buffer.

    A scratch buffer has no associated file, no swapfile, never gets written
    and never appears to be modified. The content of such a buffer is normally
    under the control of code. Direct editing is disabled.
    """
    def __init__(self, name, buffer):
        super().__init__(buffer)
        self.name = name
        self.options.buftype = 'nofile'
        self.options.swapfile = False
        self.options.modified = False
        self.options.readonly = True
        self.options.modifiable = False
        self.options.bufhidden = 'hide'

        self.options.buflisted = True

    def show(self):
        """Make this buffer visible in the current window."""
        commands.buffer(self.number, bang=True)

    def modifiable(self):
        """Create a context that allows the buffer to be modified.""" 
        return self.temp_options(modifiable=True, readonly=False)


_known_special_buffers = {}


def get_display_buffer(name):
    """Get a named display-only buffer.

    The actual buffer name will be of the form '/[[name]]'. The buffer is
    created if it does not already exist.

    :param name:
        An identifying name for this buffer.
    """
    buf_name = f'/[[{name}]]'
    b = _known_special_buffers.get(buf_name, None)
    if b is not None:
        return b

    for b in vim.buffers:
        if b.name == buf_name:
            break
    else:
        commands.new()
        b = vim.current.buffer
        commands.wincmd('c')

    b = Scratch(buf_name, b)
    _known_special_buffers[buf_name] = b
    return b


class Log:
    def __init__(self):
        self.fifo = collections.deque(maxlen=100)
        self.buf = None

    def __call__(self, *args):
        text = ' '.join(str(a) for a in args)
        lines = text.splitlines()
        self.fifo.extend(lines)
        buf = self.buf
        if buf:
            with buf.modifiable():
                buf.append(lines)
        self._trim()

    def clear(self):
        self.fifo.clear()
        self._trim()
        
    def _trim(self):
        buf = self.buf
        if buf:
            d = len(buf) - len(self.fifo)
            if d > 0:
                with buf.modifiable():
                    buf[:] = buf[d:]

    def show(self):
        """Show the buffer.

        If there is no buffer currently displaying the log then this will:

        - Split the current window.
        - Create a buffer and show it in the new split.
        """
        if self.buf is None:
            self.buf = get_display_buffer('log')
            with self.buf.modifiable():
                self.buf[:] = list(self.fifo)
        for w in vim.windows:
            if w.buffer.number == self.buf.number:
                break
        else:
            commands.wincmd('s')
            self.buf.show()
            commands.wincmd('w')

    def set_maxlen(self, maxlen):
        if maxlen != self.fifo.maxlen:
            self.fifo = collections.deque(self.fifo, maxlen)
        self._trim()


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
        this = _Struct()
        this._filter_callback = kwargs.get('filter', None)
        this._close_callback = kwargs.get('callback', None)
        if this._filter_callback:
            vim_func, this._filter_uid = _routed_function(self._on_filter)
            kwargs['filter'] = vim_func
        else:
            this._filter_uid = None
        vim_func, this._close_uid = _routed_function(self._on_close)
        kwargs['callback'] = vim_func
        this._id = func(content, kwargs)
        self.__dict__.update(this.__dict__)
        self._popups[self._id] = self

    @property
    def id(self):
        return self._id

    @property
    def buffer(self):
        return vim.buffers[vim.winbufnr(self._id)]

    def hide(self):
        vim.popup_hide(self._id)

    def show(self):
        vim.popup_show(self._id)

    def settext(self, content):
        vim.popup_settext(self._id, content)

    def setoptions(self, **options):
        vim.popup_setoptions(self._id, options)

    def getoptions(self):
        return vim.popup_getoptions(self._id)

    def end(self):
        vim.popup_close(self._id)

    def __getattr__(self, name):
        options = vim.popup_getoptions(self._id)
        return options.get(name, None)

    def __setattr__(self, name, value):
        vim.popup_setoptions(self._id, {name: value})

    def _cleanup(self):
        _routed_functions.pop(self._filter_uid, None)
        _routed_functions.pop(self._close_uid, None)
        self._popups.pop(self._id, None)

    @classmethod
    def popup_clear(cls, force):
        vim.popup_clear(force)
        active = set(vim.popup_list())
        for p in list(cls._popups.values()):
            if p.id not in active:
                p._cleanup()

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

    
class Callback:
    callbacks = {}

    def __init__(self, func, *args):
        uid = self.uid = str(next(id_source))
        self.method = None
        try:
            ref_inst = func.__self__
        except AttributeError:
            ref_inst = func
        else:
            self.method = weakref.ref(func.__func__)
        self.ref_inst = weakref.ref(
            ref_inst, functools.partial(self.on_del, uid=uid))

        self.callbacks[uid] = self
        self.args = args
        # log('CB: Add', uid)

    def __call__(self, *args):
        args = [coerce_arg(a) for a in args]
        inst = self.ref_inst()
        if inst is not None:
            method = self.method and self.method()
            if method is not None:
                return method(inst, *args)
            else:
                return inst(*args)

        self.on_del(None, uid=self.uid)
        return 0

    def kill(self):
        self.callbacks.pop(self.uid)
        # log(f'Cleanup callback {self.uid}')

    @classmethod
    def invoke(cls):
        uid = vim.vars._vpe_args_['uid']
        cb = cls.callbacks.get(uid, None)
        if cb is None:
            log(f'invoke: {uid=} not found')
            return 0
        args = vim.vars._vpe_args_['args']
        return cb(*args)

    @classmethod
    def on_del(cls, _, *, uid):
        log('Cleanup', uid)
        cls.callbacks.pop(uid, None)

    def as_call(self):
        """Format Vim script string to invoke this callback.

        More accurately, format the Vim script to call Callback.invoke with the
        appropriate parameters.
        """
        args = [quoted_string(self.uid)]
        for a in self.args:
            if isinstance(a, str):
                args.append(quoted_string(a))
            else:
                args.append(str(a))
        return f'call VPE_Call({", ".join(args)})'

    def as_vim_function(self):
        """Create a vim.Function that will route to this callback."""
        vim_func = _vim.Function('VPE_call', args=[self.uid])


class expr:
    pass


class expr_arg(expr):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return self.arg


def quoted_string(s):
    return f'"{s}"'


def coerce_arg(value):
    if isinstance(value, bytes):
        return value.decode()
    if isinstance(value, _vim_list_type):
        return [coerce_arg(el) for el in value]
    if isinstance(value, (_vim_dict_type, dictionaries.Dictionary)):
        return {k.decode(): coerce_arg(v) for k, v in value.items()}
    return value


class AutoCmdGroup:
    """Context for managing auto commands within a given group."""
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        _vim.command(f'augroup {self.name}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _vim.command('augroup END')

    def delete_all(self):
        """Delete all entries in the group."""
        _vim.command('autocmd!')

    def add(
        self, event, /, func, *, pat='<buffer>', once=False, nested=False):
        """Add a new auto command to the group.

        :param event:
            The name of the event.
        :param func:
            The Python function to invoke. Plain functions and instance methods
            are supported.
        :param pat:
            The file pattern to match. If not supplied then the special
            '<buffer>' pattern is used. If the argument is a Buffer then
            the special patern for 'buffer=N> is used.
        :param once, nested:
            The standard ':autocmd' options.
        """
        if isinstance(pat, buffers.Buffer):
            pat = f'<buffer={pat.number}>'
        cmd_seq = ['autocmd', event, pat]
        if once:
            cmd_seq.append('++once')
        if nested:
            cmd_seq.append('++nested')
        cmd_seq.append(Callback(func).as_call())
        _vim.command(' '.join(cmd_seq))


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
    _convert_colour_names(kwargs)
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


def _convert_colour_names(kwargs):
    _cterm_argnames = set(('ctermfg', 'ctermbg', 'ctermul'))
    _gui_argnames = set(('guifg', 'guibg', 'guisp'))
    for arg_name, name in kwargs.items():
        if name in _std_vim_colours:
            continue
        if name in _cterm_argnames:
            kwargs[name] = colors.name_to_number.get(name.lower(), name)
        elif name in _gui_argnames:
            kwargs[name] = colors.name_to_hex.get(name.lower(), name)


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


def popup_filter_yesno(id, key_str):
    return vim.popup_filter_yesno(id, key_str)


def popup_filter_menu(id, key_str):
    if key_str != b' ':
        # TODO: In Python land, we seem to get a mysterious initial <space> key
        #       that immediately causes first item to be selected and the menu
        #       to close. This work-around simply blocks the <space> key.
        return vim.popup_filter_menu(id, key_str)
    return False


def popup_clear(force=False):
    PopupWindow.popup_clear(force)


def _admin_status():
    """Useful, but unspported, diagnostic."""

    log(f'{len(Timer._timers)=}')
    log(f'{len(PopupWindow._popups)=}')
    log(f'{len(_routed_functions)=}')


def wrap_item(item):
    wrapper = _wrappers.get(type(item), None)
    if wrapper is not None:
        return wrapper(item)
    elif isinstance(item, bytes):
        return item.decode()
    return item


# Create a Vim and Log instance for general use.
vim = Vim()
log = Log()

_wrappers = {
    type(_vim.options): options.Options,
    type(_vim.windows): windows.Windows,
    _vim.Buffer: _get_wrapped_buffer,
    _vim.Dictionary:    dictionaries.Dictionary,
    _vim.Range: buffers.Range,
    _vim.TabPage: tabpages.TabPage,
    _vim.Window: windows.Window,
}
