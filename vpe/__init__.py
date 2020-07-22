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
import functools
import itertools
import pathlib
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

_known_special_buffers = {}


def _get_wrapped_buffer(vim_buffer):
    b = buffers.Buffer.get_known(vim_buffer)
    if b is None:
        b = buffers.Buffer(vim_buffer)
    return b


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


def get_display_buffer(name, create=True):
    """Get a named display-only buffer.

    The actual buffer name will be of the form '/[[name]]'. By default, the
    buffer is created if it does not already exist.

    :param name:
        An identifying name for this buffer.
    :param existing:
        This can be set false to prevent creation if the buffer does not
        already exist.
    """
    buf_name = f'/[[{name}]]'
    b = _known_special_buffers.get(buf_name, None)
    if b is not None:
        return b

    for b in vim.buffers:
        if b.name == buf_name:
            break
    else:
        if not create:
            return
        commands.new()
        b = vim.current.buffer
        commands.wincmd('c')

    b = Scratch(buf_name, b)
    _known_special_buffers[buf_name] = b
    return b


class Log:
    def __init__(self):
        self.fifo = collections.deque(maxlen=1000)
        self.buf = get_display_buffer('log', create=False)

    def __call__(self, *args):
        text = ' '.join(str(a) for a in args)
        lines = text.splitlines()
        self.fifo.extend(lines)
        buf = self.buf
        if buf:
            with buf.modifiable():
                buf.append(lines)
        self._trim()
        if self.buf:
            for w in vim.windows:
                if w.buffer.number == self.buf.number:
                    vim.win_execute(vim.win_getid(w.number), '$')

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
        cb = Callback(self._invoke_self)
        self._id = vim.timer_start(ms, cb.as_vim_function(), kwargs)
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

    def _invoke_self(self, _):
        if self.repeat == 1:
            self._cleanup()
        self.callback(self)

    def _cleanup(self):
        self._timers.pop(self.id, None)

    @classmethod
    def stop_all(cls):
        vim.timer_stopall()
        for timer in list(cls._timers.values()):
            timer._cleanup()


class _PopupAttr(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, _):
        return vim.popup_getoptions(obj.id)[self.name]

    def __set__(self, obj, value):
        vim.popup_setoptions(obj.id, {self.name: value})


_popup_options = (
    'line', 'col', 'pos', 'posinvert', 'textprop', 'textpropwin', 'textpropid',
    'fixed', 'flip', 'maxheight', 'minheight', 'maxwidth', 'minwidth',
    'firstline', 'hidden', 'tabpage', 'title', 'wrap', 'drag', 'resize',
    'highlight', 'padding', 'border', 'borderhighlight',
    'borderchars', 'scrollbar', 'scrollbarhighlig', 'thumbhighlight', 'zindex',
    'mask', 'time', 'moved', 'mousemoved', 'cursorline', 'mapping',
    'filtermode',
)

def _add_popup_options_properties(cls):
    for name in _popup_options:
        setattr(cls, name, _PopupAttr(name))
    setattr(cls, 'close_control', _PopupAttr('close'))
    return cls


@_add_popup_options_properties
class Popup:
    _popups = {}
    _create_func = 'popup_create'

    def __init__(self, content, **kwargs):
        close_cb = Callback(self._on_close)
        filter_cb = Callback(self._on_key, pass_bytes=True)
        kwargs['callback'] = close_cb.as_vim_function()
        kwargs['filter'] = filter_cb.as_vim_function()
        self._id = getattr(vim, self._create_func)(content, kwargs)
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

    def close(self):
        vim.popup_close(self._id)

    @classmethod
    def popup_clear(cls, force):
        vim.popup_clear(force)
        active = set(vim.popup_list())
        for p in list(cls._popups.values()):
            if p.id not in active:
                cls._popups.pop(p.id, None)

    def on_close(self, close_arg):
        pass

    def on_key(self, key, byte_seq):
        pass

    def _on_close(self, _, close_arg):
        self.on_close(close_arg)
        self._popups.pop(self._id, None)

    def _on_key(self, _, key_bytes):
        for byte_seq in self._split_key_sequences(key_bytes):
            k = _special_keymap.get(byte_seq, byte_seq)
            if isinstance(k, bytes):
                try:
                    k = k.decode()
                except UnicodeError:
                    pass
                else:
                    k = _special_keymap.get(k, k)
            ret = self.on_key(k, byte_seq)
        return ret

    @staticmethod
    def _split_key_sequences(s):
        s_char = b'\x80'
        if not s.startswith(s_char):
            yield s
            return
        while s:
            prefix, sep, s = s.partition(s_char)
            if prefix:
                yield s_char + prefix


class PopupAtCursor(Popup):
    """Popup configured to appear near the cursor.

    This creates the popup using popup_atcursor().
    """
    _create_func = 'popup_atcursor'


class PopupBeval(Popup):
    """Popup configured to appear near (v:beval_line, v:beval_col).

    This creates the popup using popup_beval().
    """
    _create_func = 'popup_beval'


class PopupNotification(Popup):
    """Popup configured as a short lived notification (default 3s).

    This creates the popup using popup_notification().
    """
    _create_func = 'popup_notification'


class PopupDialog(Popup):
    """Popup configured as a dialogue.

    This creates the popup using popup_dialog().
    """
    _create_func = 'popup_dialog'

    def on_key(self, key, byte_seq):
        return vim.popup_filter_yesno(self.id, byte_seq)


class PopupMenu(Popup):
    """Popup configured as a menu.

    This creates the popup using popup_menu().
    """
    _create_func = 'popup_menu'

    def on_key(self, key, byte_seq):
        return vim.popup_filter_menu(self.id, byte_seq)


class Function(_vim.Function):
    """Wrapper around a vim.Function.

    This provides some minimal cooercion of function return types.

    - A vim.Dictionary is wrapped as a VPE Dictionary.
    - A bytes instance is decodes to a string, if possible.
    """
    def __call__ (self, *args, **kwargs):
        v = super().__call__(*args, **kwargs)
        if isinstance(v, _vim.Dictionary):
            return dictionaries.Dictionary(v)
        elif isinstance(v, bytes):
            try:
                return v.decode()
            except UnicodeError:
                return v
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

    def __init__(
            self, func, *, py_args=(), py_kwargs={}, vim_args=(),
            pass_bytes=False):
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
        self.vim_args = vim_args
        self.py_args = py_args
        self.py_kwargs = py_kwargs
        self.pass_bytes = pass_bytes

    def __call__(self, *vim_args):
        inst = self.ref_inst()
        if inst is not None:
            vim_args = [
                coerce_arg(a, keep_bytes=self.pass_bytes) for a in vim_args]
            method = self.method and self.method()
            if method is not None:
                return method(inst, *self.py_args, *vim_args)
            else:
                return inst(*self.py_args, *vim_args)

        self.on_del(None, uid=self.uid)
        return 0

    def kill(self):
        self.callbacks.pop(self.uid)

    @classmethod
    def invoke(cls):
        uid = vim.vars._vpe_args_['uid']
        cb = cls.callbacks.get(uid, None)
        if cb is None:
            return 0
        vim_args = vim.vars._vpe_args_['args']
        ret = cb(*vim_args)
        if ret is None:
            ret = 0
        return ret

    @classmethod
    def on_del(cls, _, *, uid):
        cls.callbacks.pop(uid, None)

    def as_invocation(self):
        """Format a command of the form 'VPE_Call(...)'

        The result is a valid Vim script expression.
        """
        vim_args = [quoted_string(self.uid)]
        for a in self.vim_args:
            if isinstance(a, str):
                vim_args.append(quoted_string(a))
            else:
                vim_args.append(str(a))
        return f'VPE_Call({", ".join(vim_args)})'

    def as_call(self):
        """Format a command of the form 'call VPE_Call(...)'

        The result can be used as a colon prompt command.
        """
        return f'call {self.as_invocation()}'

    # TODO: This form ignores the vim_args.
    def as_vim_function(self):
        """Create a vim.Function that will route to this callback."""
        return _vim.Function('VPE_Call', args=[self.uid])


class expr:
    pass


class expr_arg(expr):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return self.arg


def quoted_string(s):
    return f'"{s}"'


def coerce_arg(value, keep_bytes=False):
    if isinstance(value, bytes) and not keep_bytes:
        try:
            return value.decode()
        except UnicodeError:
            return value
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


# TODO: Need to think about mapping API. This is probably sub-optimal.
def nmap(keys, func, curbuf=True):
    """Set up a normal mapping that invokes a Python function.

    :param keys:
        The key sequence to be mapped.
    :param func:
        The Python function other callable to invoke for the mapping.
    :param curbuf:
        Set to false is the mapping should *not* be restricted to the current
        buffer.
    """
    cb = Callback(func)
    # sw_normal = '<c-\\><c-n>'
    buffer = '<buffer> ' if curbuf else ''
    # rhs = f'{sw_normal}:silent {cb.as_call()}<CR>'
    rhs = f':silent {cb.as_call()}<CR>'
    cmd = f'nnoremap {buffer} {keys} {rhs}'
    vim.command(cmd)


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


def popup_clear(force=False):
    Popup.popup_clear(force)


def _admin_status():
    """Useful, but unspported, diagnostic."""

    log(f'{len(Timer._timers)=}')
    log(f'{len(Popup._popups)=}')
    log(f'{len(Callback.callbacks)=}')
    log(f'{len(Timer._timers)=}')


def wrap_item(item):
    wrapper = _wrappers.get(type(item), None)
    if wrapper is not None:
        return wrapper(item)
    elif isinstance(item, bytes):
        try:
            return item.decode()
        except UnicodeError:
            return item
    return item


_wrappers = {
    type(_vim.options): options.Options,
    type(_vim.windows): windows.Windows,
    _vim.Buffer: _get_wrapped_buffer,
    _vim.Dictionary:    dictionaries.Dictionary,
    _vim.Range: buffers.Range,
    _vim.TabPage: tabpages.TabPage,
    _vim.Window: windows.Window,
}

# Create a Vim and Log instance for general use.
vim = Vim()
log = Log()

_special_keymap = {}

_special_key_names = (
    'Up', 'Down', 'Left', 'Right', 'Help', 'Undo', 'Insert',
    'Home', 'End', 'PageUp', 'PageDown', 'kHome', 'kEnd',
    'kPageUp', 'kPageDown', 'kPlus', 'kMinus', 'kMultiply',
    'kDivide', 'kEnter', 'kPoint',
    'LeftMouse', 'LeftDrag', 'LeftRelease', 'MiddleMouse',
    'MiddleDrag', 'MiddleRelease', 'RightMouse', 'RightDrag',
    'RightRelease', 'X1Mouse', 'X1Drag', 'X1Release',
    'X2Mouse', 'X2Drag', 'X2Release',
    'ScrollWheelUp', 'ScrollWheelDown',
)

def _register_key(name, unmodified=True, modifiers='SCMA'):
    if unmodified:
        key_name = f'<{name}>'
        _vim.command(rf'let g:_vpe_temp_ = "\{key_name}"')
        _special_keymap[vim.vars._vpe_temp_] = key_name
    for m in modifiers:
        key_name = f'<{m}-{name}>'
        _vim.command(rf'let g:_vpe_temp_ = "\{key_name}"')
        _special_keymap[vim.vars._vpe_temp_] = key_name


for k in _special_key_names:
    _register_key(k)
for n in range(12):
    _register_key(f'F{n + 1}')
for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
    _register_key(c, unmodified=False, modifiers='CMA')
del _special_key_names, _register_key
