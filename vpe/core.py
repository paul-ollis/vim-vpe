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

    This is in instance of the `Log` class.
"""
# pylint: disable=too-many-lines

from __future__ import annotations

from typing import Optional, Any, Tuple, Dict
import collections
import functools
import io
import itertools
import sys
import time
import traceback
import weakref

import vim as _vim

from . import colors
from . import commands
from . import common
from . import wrappers

__api__ = [
    'expr_arg', 'Callback',
]
__shadow_api__ = [
    '_VimDesc',
]
__all__ = [
    'AutoCmdGroup', 'Timer', 'Popup', 'PopupAtCursor', 'PopupBeval',
    'PopupNotification', 'PopupDialog', 'PopupMenu',
    'Log', 'error_msg', 'call_soon', 'log',
    'saved_winview', 'highlight', 'pedit', 'popup_clear',
    'timer_stopall', 'find_buffer_by_name', 'feedkeys', 'get_display_buffer',
    *__api__
]
id_source = itertools.count()

# Set up some global Vim variables to support type testing.
_vim.command('let g:_vpe_example_list_ = []')
_vim.command('let g:_vpe_example_dict_ = {}')
# pylint: disable=invalid-name
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

#: Dictionary to track any special buffers that get created.
_known_special_buffers: dict = {}

_special_keymap: dict = {}

_vim_func_defs = """
function! VPE_Call(uid, ...)
    let g:_vpe_args_ = {}
    let g:_vpe_args_['uid'] = a:uid
    let g:_vpe_args_['args'] = a:000
    return py3eval('vpe.Callback.invoke()')
endfunction
"""
_vim.command(_vim_func_defs)


class Scratch(wrappers.Buffer):
    """A scratch buffer.

    A scratch buffer has no associated file, has no swap file, never gets
    written and never appears to be modified. The content of such a buffer is
    typically under the control of plugin code. Direct editing is disabled.

    Direct instantiation is not recommended; use `get_display_buffer`, which
    creates bufferes with suitably formatted names.
    """
    def __init__(self, name, buffer):
        super().__init__(buffer)
        self.name = name
        options = self.options
        options.buftype = 'nofile'
        options.swapfile = False
        options.modified = False
        options.readonly = True
        options.modifiable = False
        options.bufhidden = 'hide'
        options.buflisted = True

    def show(self) -> None:
        """Make this buffer visible in the current window."""
        commands.buffer(self.number, bang=True)

    def modifiable(self) -> wrappers.TemporaryOptions:
        """Create a context that allows the buffer to be modified."""
        return self.temp_options(modifiable=True, readonly=False)


def get_display_buffer(name: str) -> Scratch:
    """Get a named display-only buffer.

    The actual buffer name will be of the form '/[[name]]'. The
    buffer is created if it does not already exist.

    :name:     An identifying name for this buffer.
    """
    # pylint: disable=unsubscriptable-object
    buf_name = f'/[[{name}]]'
    b = _known_special_buffers.get(buf_name, None)
    if b is not None:
        return b

    for b in wrappers.vim.buffers:
        if b.name == buf_name:
            break
    else:
        commands.new()
        b = wrappers.vim.current.buffer
        commands.wincmd('c')

    b = Scratch(buf_name, b)
    _known_special_buffers[buf_name] = b
    return b


class Log:
    """Support for logging to a display buffer.

    An instance of this class provides a mechanism to support logging that can
    be viewed within a buffer. Instances of this class act as a simple print
    function.:<py>:

        info = Log('my_info')
        info("Created log", info)
        info("Starting process")

    The output is stored in a Python FIFO structure, up to a maximum number
    of lines; the default is 100, change this with `set_maxlen`. No actual Vim
    buffer is created until required, which is when `show` is first
    invoked.:<py>:

        info.show()   # Make the log visible.

    The :mod:`vpe` module provides a predefined log, called 'VPE'. This is
    available for general use. VPE also uses it to log significant occurrences
    - mainly error conditions.

    :name:   A name that maps to the corresponding display buffer.
    :maxlen: The maximum number of lines to store.

    @buf: The corresponding Vim buffer. This will be ``None`` if the `show`
          method has never been invoked.
    """
    def __init__(self, name, maxlen=500):
        self.fifo = collections.deque(maxlen=maxlen)
        self.name = name
        self.buf = None
        self.start_time = time.time()
        self.text_buf = io.StringIO()
        self.saved_out = []

    def __call__(self, *args):
        """Write to the log.

        The arguments are formatted using ``print`` and then appended to the
        log buffer, with a time stamp.

        :args: The same as for Python's print function.
        """
        print(*args, file=self.text_buf)
        self._flush_lines()

    def redirect(self):
        """Redirect stdout/stderr to the log."""
        self.saved_out.append((sys.stdout, sys.stderr))
        sys.stdout = sys.stderr = self

    def unredirect(self):
        """Undo most recent redirection."""
        if self.saved_out:
            sys.stdout, sys.stderr = self.saved_out.pop()

    def _flush_lines(self):  # pylint: disable=too-many-branches
        t = time.time()
        lines = []
        part_line = ''
        for i, line in enumerate(self.text_buf.getvalue().splitlines(True)):
            if line[-1:] != '\n':
                part_line = line
                break
            if i == 0:
                prefix = f'{t - self.start_time:7.2f}:'
            else:
                prefix = ' ' * 8
            lines.append(f'{prefix} {line}')
        self.text_buf = io.StringIO(part_line)
        self.text_buf.seek(0, io.SEEK_END)

        self.fifo.extend(lines)
        buf = self.buf
        if buf:
            with buf.modifiable():
                buf.append(lines)
        self._trim()
        win_execute = wrappers.vim.win_execute
        if self.buf:
            for w in wrappers.vim.windows:
                if w.buffer.number == self.buf.number:
                    win_execute(wrappers.vim.win_getid(w.number), '$|redraw')

    def flush(self):
        """File like I/O support."""

    def write(self, s):
        """Write a string to the log buffer.

        :s: The string to write.
        """
        self.text_buf.write(s)
        self._flush_lines()

    def clear(self) -> None:
        """Clear all lines from the log.

        The FIFO is cleared and the corresponding buffer updated.
        """
        self.fifo.clear()
        self._trim()

    def _trim(self) -> None:
        buf = self.buf
        if buf:
            d = len(buf) - len(self.fifo)
            if d > 0:
                with buf.modifiable():
                    buf[:] = buf[d:]

    def show(self) -> None:
        """Make sure the buffer is visible.

        If there is no buffer currently displayed the log then this will:

        - Split the current window.
        - Create a buffer and show it in the new split.
        """
        if self.buf is None:
            self.buf = get_display_buffer(self.name)
            with self.buf.modifiable():
                self.buf[:] = list(self.fifo)
        for w in wrappers.vim.windows:
            if w.buffer.number == self.buf.number:
                break
        else:
            commands.wincmd('s')
            self.buf.show()
            commands.wincmd('w')

    def set_maxlen(self, maxlen: int) -> None:
        """Set the maximum length of the log's FIFO.

        This will discard older lines if necessary.

        :maxlen: How many lines to store in the FIFO.
        """
        if maxlen != self.fifo.maxlen:
            self.fifo = collections.deque(self.fifo, maxlen)
        self._trim()


class Timer:
    """Pythonic way to use Vim's timers.

    This can be used as a replacement for the vim functions: timer_start,
    timer_info, timer_pause, timer_stop.

    An example of usage:<py>:

        def handle_expire(t):
            print(f'{t.repeat=}')

        # This will cause handle_expire to be called twice. The output will be:
        #     t.repeat=2
        #     t.repeat=1
        t = Timer(ms=100, handle_expire, repeat=2)

    The status of a timer can be queried using the properties `time`, `repeat`,
    `remaining` and `paused`. The methods `pause`, `stop` and `resume` allow
    an active timer to be controlled.

    :ms:     The timer's interval in milliseconds.
    :func:   The function to be invoked when the timer fires. This is
             called with the firing `Timer` instance as the only parameter.
    :repeat: How many times to fire.
    """
    _timers: dict = {}

    def __init__(self, ms, func, repeat=None):
        cb = Callback(self._invoke_self)
        t_options = {}
        if repeat is not None:
            t_options['repeat'] = repeat
        self._id = wrappers.vim.timer_start(
            ms, cb.as_vim_function(), t_options)
        self._timers[self._id] = self
        self._callback = func

    @property
    def id(self) -> int:
        """The ID of the underlying vim timer."""
        return self._id

    @property
    def time(self) -> int:
        """The time value used to create the timer."""
        return self._get_info('time')

    @property
    def repeat(self) -> int:
        """The number of times the timer will still fire."""
        return self._get_info('repeat')

    @property
    def remaining(self) -> int:
        """The time remaining (ms) until the timer will next fire."""
        return self._get_info('remaining')

    @property
    def paused(self) -> bool:
        """True if the timer is currently paused."""
        return bool(self._get_info('paused'))

    def _get_info(self, name):
        info = wrappers.vim.timer_info(self.id)
        return info[0][name] if info else None

    def stop(self):
        """Stop the timer.

        This invokes vim's timer_stop function.
        """
        wrappers.vim.timer_stop(self.id)
        self._cleanup()

    def pause(self):
        """Pause the timer.

        This invokes vim's timer_pause funciton.
        """
        wrappers.vim.timer_pause(self.id, True)

    def resume(self):
        """Resume the timer, if paused.

        This invokes vim's timer_pause funciton.
        """
        wrappers.vim.timer_pause(self.id, False)

    def _invoke_self(self, _):
        if self.repeat == 1:
            self._cleanup()
        self._callback(self)

    def _cleanup(self):
        self._timers.pop(self.id, None)

    @classmethod
    def stop_all(cls):
        """Stop all timers and clean up.

        Use this in preference to vim.timer_stopall, to ensure that VPE cleans
        up its underlying administrative structures.
        """
        wrappers.vim.timer_stopall()
        for timer in list(cls._timers.values()):
            timer._cleanup()  # pylint: disable=protected-access


class _PopupOption:
    # pylint: disable=too-few-public-methods
    def __init__(self, name):
        self.name = name


class _PopupROOption(_PopupOption):
    # pylint: disable=too-few-public-methods
    def __get__(self, obj, _):
        return wrappers.vim.popup_getoptions(obj.id)[self.name]


class _PopupWOOption(_PopupOption):
    # pylint: disable=too-few-public-methods
    def __set__(self, obj, value):
        wrappers.vim.popup_setoptions(obj.id, {self.name: value})


class _PopupRWOption(_PopupROOption, _PopupWOOption):
    # pylint: disable=too-few-public-methods
    pass


class _PopupROPos(_PopupOption):
    # pylint: disable=too-few-public-methods
    def __get__(self, obj, _):
        return wrappers.vim.popup_getpos(obj.id)[self.name]


class _PopupWOPos(_PopupOption):
    # pylint: disable=too-few-public-methods
    def __set__(self, obj, value):
        wrappers.vim.popup_move(obj.id, {self.name: value})


class _PopupRWPos(_PopupROPos, _PopupWOPos):
    # pylint: disable=too-few-public-methods
    pass


class Popup:
    """A Pythonic way to uses Vim's popup windows.

    This can be used as instead of the individual functions popup_create,
    popup_hide, popup_show, popup_settext, popup_close).

    Creation of a Popup uses vim.popup_create to create the actual popup
    window. Control of the popup windows is achieved using the methods `hide`,
    `show` and `settext`. You can subclass this in order to override the
    `on_close` or `on_key` methods.

    The subclasses `PopupAtCursor`, `PopupBeval`, `PopupNotification`,
    `PopupDialog` and `PopupMenu`, provide similar convenient alternatives
    to popup_atcursor, popup_beval, popup_notification, popup_dialog and
    popup_menu.

    The windows options (line, col, pos, *etc*.) are made avaiable as
    properties of the same name. For example, to change the first displated
    line:<py>:

        p = vpe.Popup(my_text)
        ...
        p.firstline += 3

    The close option must be accessed as close_control, because `close` is a
    Popup method. There is no filter or callback property.

    :content:   The content for the window.
    :p_options: Nearly all the standard popup_create options (line, col, pos
                *etc*. can be provided as keyword arguments. The exceptions
                are filter and callback. Over ride the `on_key` and `on_close`
                methods instead.
    """
    _popups: dict = {}
    _create_func = 'popup_create'

    def __init__(self, content, **p_options):
        close_cb = Callback(self._on_close)
        filter_cb = Callback(self._on_key, pass_bytes=True)
        p_options['callback'] = close_cb.as_vim_function()
        p_options['filter'] = filter_cb.as_vim_function()
        self._id = getattr(wrappers.vim, self._create_func)(content, p_options)
        self._popups[self._id] = weakref.ref(
            self, functools.partial(self._on_del, win_id=self._id))
        self._clean_up()
        self.result = -1

    @property
    def id(self) -> int:
        """The ID of the Vim popup window."""
        return self._id

    @property
    def buffer(self) -> wrappers.Buffer:
        """The buffer holding the window's content."""
        return wrappers.vim.buffers[wrappers.vim.winbufnr(self._id)]

    @classmethod
    def _on_del(cls, _, win_id):
        cls._clean_up()

    def hide(self) -> None:
        """Hide the popup."""
        wrappers.vim.popup_hide(self._id)

    def show(self) -> None:
        """Show the popup."""
        wrappers.vim.popup_show(self._id)

    def settext(self, content) -> None:
        """Set the text of the popup."""
        wrappers.vim.popup_settext(self._id, content)

    def close(self, result: int = 0) -> None:
        """Close the popup.

        :result: The result value that will be forwarded to on_close.
        """
        wrappers.vim.popup_close(self._id, result)

    @classmethod
    def clear(cls, force: bool) -> None:
        """Clear all popups from display.

        Use this in preference to vim.popup_clear, to ensure that VPE cleans
        up its underlying administrative structures.

        :force: If true then if the current window is a popup, it will also be
                closed.
        """
        wrappers.vim.popup_clear(force)
        cls._clean_up()

    @classmethod
    def _clean_up(cls):
        active = set(wrappers.vim.popup_list())
        for win_id, p_ref in list(cls._popups.items()):
            p = p_ref()
            if p is None:
                if win_id in active:
                    wrappers.vim.popup_close(win_id)
                cls._popups.pop(win_id)

    def on_close(self, result: int) -> None:
        """Invoked when the popup is closed.

        The default implementation does nothing, it is intended that this be
        over-ridden in subclasses.

        :result: The value passed to `close`. This will be -1 if the user
                 forcefully closed the popup.
        """

    def on_key(self, key: str, byte_seq: bytes) -> bool:
        """Invoked when the popup receives a keypress.

        The default implementation does nothing, it is intended that this be
        over-ridden in subclasses. The keystream is preprocessed before this
        is method is invoked as follows:

        - Merged key sequences are split, so that this is always invoked
          with the sequence for just a single key.
        - Special key sequences are converted to the standard Vim symbolic
          names such as <Up>, <LeftMouse>, <F11>, <S-F3>, <C-P>, *etc*.
        - Anything that does not convert to a special name is decoded to a
          Python string, if possible.

        :key:      The pressed key. This is typically a single character
                   such as 'a' or a symbolic Vim keyname, such as '<F1>'.
        :byte_seq: The unmodified byte sequence, as would be received for
                   a filter callback using Vimscript.
        :return:   True if the key should be considered consumed.
        """
        # pylint: disable=unused-argument,no-self-use
        return False

    def _on_close(self, _, close_arg):
        self.result = close_arg
        self.on_close(close_arg)
        self._popups.pop(self._id, None)

    def _on_key(self, _, key_bytes: bytes) -> bool:
        for byte_seq in self._split_key_sequences(key_bytes):
            k = _special_keymap.get(byte_seq, byte_seq)
            if isinstance(k, bytes):
                try:
                    k = k.decode()
                except UnicodeError:                         # pragma: no cover
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
            prefix, _, s = s.partition(s_char)
            if prefix:
                yield s_char + prefix

    borderchars = _PopupWOOption('borderchars')
    borderhighlight = _PopupRWOption('borderhighlight')
    border = _PopupRWOption('border')
    col = _PopupRWPos('col')
    core_col = _PopupROPos('core_col')
    core_line = _PopupROPos('core_line')
    core_width = _PopupROPos('core_width')
    cursorline = _PopupWOOption('cursorline')
    drag = _PopupWOOption('drag')
    firstline = _PopupRWOption('firstline')
    fixed = _PopupWOOption('fixed')
    flip = _PopupWOOption('flip')
    height = _PopupROPos('height')
    highlight = _PopupWOOption('highlight')
    lastline = _PopupROPos('lastline')
    line = _PopupRWPos('line')
    mapping = _PopupWOOption('mapping')
    mask = _PopupWOOption('mask')
    maxheight = _PopupWOOption('maxheight')
    maxwidth = _PopupWOOption('maxwidth')
    minheight = _PopupWOOption('minheight')
    minwidth = _PopupWOOption('minwidth')
    mousemoved = _PopupROOption('mousemoved')
    moved = _PopupRWOption('moved')
    padding = _PopupRWOption('padding')
    pos = _PopupWOPos('pos')
    resize = _PopupRWOption('resize')
    scrollbar = _PopupROPos('scrollbar')
    scrollbarhighlight = _PopupRWOption('scrollbarhighlight')
    scrollbar = _PopupROPos('scrollbar')
    tabpage = _PopupROOption('tabpage')
    textprop = _PopupROOption('textprop')
    textpropid = _PopupROOption('textpropid')
    textpropwin = _PopupROOption('textpropwin')
    thumbhighlight = _PopupRWOption('thumbhighlight')
    time = _PopupWOOption('time')
    title = _PopupWOOption('title')
    visible = _PopupROPos('visible')
    width = _PopupROPos('width')
    wrap = _PopupWOOption('wrap')
    zindex = _PopupRWOption('zindex')
    close_control = _PopupRWOption('close')


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

    This creates the popup using popup_dialog(). It also provides a default
    `PopupDialog.on_key` implementation that invokes popup_filter_yesno.
    """
    _create_func = 'popup_dialog'

    def on_key(self, key, byte_seq):
        """Invoke popup_filter_yesno to handle keys for this popup."""
        return wrappers.vim.popup_filter_yesno(self.id, byte_seq)


class PopupMenu(Popup):
    """Popup configured as a menu.

    This creates the popup using popup_menu(). It also provides a default
    `PopupMenu.on_key` implementation that invokes popup_filter_menu.
    """
    _create_func = 'popup_menu'

    def on_key(self, key, byte_seq):
        """Invoke popup_filter_menu to handle keys for this popup."""
        return wrappers.vim.popup_filter_menu(self.id, byte_seq)


class Callback:
    """Wrapper for a function to be called from Vim.

    :func:       The function to be invoked.
    :py_args:    Positional arguments for the function.
    :py_kwargs:  Keyword arguments for the function.
    :vim_args:   Positional arguments for helper Vim function.
    :pass_bytes: If true then vim byte-strings will not be decoded to Python
                 strings.
    :info:       Additional info to store with the callback.
                 TODO: Only really for MapCallback!
    """
    # pylint: disable=too-many-instance-attributes
    callbacks: dict = {}
    caller = 'VPE_Call'

    def __init__(
            self, func, *, py_args=(), py_kwargs={}, vim_args=(),
            pass_bytes=False, info=()):
        # pylint: disable=dangerous-default-value
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
        self.py_kwargs = py_kwargs.copy()
        self.pass_bytes = pass_bytes
        self.info = info

    def __call__(self, vim_args, callargs=()):
        inst = self.ref_inst()
        if inst is not None:
            vim_args = [
                coerce_arg(a, keep_bytes=self.pass_bytes) for a in vim_args]
            method = self.method and self.method()
            if method is not None:
                return method(
                    inst, *callargs, *self.py_args, *vim_args,
                    **self.py_kwargs)
            return inst(
                *callargs, *self.py_args, *vim_args, **self.py_kwargs)

        self.on_del(None, uid=self.uid)
        return 0

    @classmethod
    def invoke(cls):
        """Invoke this callback function."""
        try:
            uid = wrappers.vim.vars['_vpe_args_']['uid']
            cb = cls.callbacks.get(uid, None)
            if cb is None:
                log(f'{uid=} is dead!')
                return 0

            vim_args = _vim.vars['_vpe_args_']['args']
            ret = cb(vim_args)
            if ret is None:
                ret = 0
            return ret

        except Exception as e:  # pylint: disable=broad-except
            log(f'{e.__class__.__name__} {e}')
            traceback.print_exc(file=log)

        return -1

    @classmethod
    def on_del(cls, _, *, uid):
        """"Handle deletion of weak reference to method's instance."""
        cls.callbacks.pop(uid, None)

    def as_invocation(self):
        """Format a command of the form 'VPE_xxx(...)'

        The result is a valid Vim script expression.
        """
        vim_args = [quoted_string(self.uid)]
        for a in self.vim_args:
            if isinstance(a, str):
                vim_args.append(quoted_string(a))
            else:
                vim_args.append(str(a))
        return f'{self.caller}({", ".join(vim_args)})'

    def as_call(self):
        """Format a command of the form 'call VPE_xxx(...)'

        The result can be used as a colon prompt command.
        """
        return f'call {self.as_invocation()}'

    # TODO: This form ignores the vim_args.
    def as_vim_function(self):
        """Create a vim.Function that will route to this callback."""
        return _vim.Function(f'{self.caller}', args=[self.uid])


class expr_arg:
    """Wrapper for a Vim argument that is an expression.

    This is used to wrap a string that represents an expression that should be
    passed to a Vim function, without being quoted.

    :arg: The argument as a string representing the Vim expression.
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, arg: str):
        self.arg = arg

    def __str__(self):
        return self.arg


def quoted_string(s: str) -> str:
    """Wrap a Vim argument in double quotation marks.

    :s:      The string to be wrapped.
    :return: The string inside double quotes.
    """
    return f'"{s}"'


def coerce_arg(value: Any, keep_bytes=False) -> Any:
    """Coerce a Vim value to a more natural Python value.

    :value:      The value to coerce.
    :keep_bytes: If true then a bytes value is not decoded to a string.
    :return:
        type == bytes
            Unless keep_bytes is set this is decoded to a Python string, if
            possible. If decoding fails, the bytes value is returned.
        type == vim list
            All items in the list are (recursively) coerced.
        type == vim dictionary
            All keys are decoded and all values are (recursively) coerced.
            Failre to decode a key will raise UnicodeError.
    :raise UnicodeError:
        If a dictionay key cannot be decoded.
    """
    if isinstance(value, bytes) and not keep_bytes:
        try:
            return value.decode()
        except UnicodeError:                                 # pragma: no cover
            return value
    try:
        value = value._proxied  # pylint: disable=protected-access
    except AttributeError:
        pass
    if isinstance(value, _vim_list_type):
        return [coerce_arg(el) for el in value]
    if isinstance(value, (_vim_dict_type, wrappers.MutableMappingProxy)):
        return {k.decode(): coerce_arg(v) for k, v in value.items()}
    return value


def build_dict_arg(*pairs: Tuple[str, Any]) -> Dict[str, Any]:
    """Build a dictionary argument for a Vim function.

    This takes a list of name, value pairs and builds a corresponding
    dictionary. Entries with a value of ``None`` are not added to the
    dictionary.

    :pairs: The list if name, value pairs.
    """
    return {name: value for name, value in pairs if value is not None}


class AutoCmdGroup:
    """A Pythonic way to define auto commands.

    This is a context manager that supports definition of autocommands
    that:

    - Are always in a given group.
    - Invoke Python code when triggered.

    It is intended to be used as:<py>:

        with AutoCmdGroup('mygroup') as g:
            g.delete_all()
            g.add('BufWritePre', handle_bufwrite, ...)
            g.add('BufDelete', handle_bufdelete, ...)

        ...

        # Add more autocommands to the same group.
        with AutoCmdGroup('mygroup') as g:
            g.delete_all()
            g.add('BufWritePre', handle_bufwrite, ...)

    :name: The name of the group.
    """
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        common.vim_command(f'augroup {self.name}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        common.vim_command('augroup END')

    @staticmethod
    def delete_all():
        """Delete all entries in the group."""
        common.vim_command('autocmd!')

    @staticmethod
    def add(event, /, func, *, pat='<buffer>', once=False, nested=False):
        """Add a new auto command to the group.

        :event:  The name of the event.
        :func:   The Python function to invoke. Plain functions and instance
                 methods are supported.
        :pat:    The file pattern to match. If not supplied then the special
                 '<buffer>' pattern is used. If the argument is a `Buffer` then
                 the special pattern for 'buffer=N> is used.
        :once:   The standard ':autocmd' options.
        :nested: The standard ':autocmd' options.
        """
        if isinstance(pat, wrappers.Buffer):
            pat = f'<buffer={pat.number}>'
        cmd_seq = ['autocmd', event, pat]
        if once:
            cmd_seq.append('++once')
        if nested:
            cmd_seq.append('++nested')
        cmd_seq.append(Callback(func).as_call())
        common.vim_command(' '.join(cmd_seq))


def highlight(
        *, group=None, clear=False, default=False, link=None, disable=False,
        **kwargs):
    """Python version of the highlight command.

    This provides keyword arguments for all the command parameters. These are
    generally taken from the :vim:`:highlight` command's documentation.

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
        If set then the generated command has the form ``highlight
        default...``.

    :kwargs:
        The remain keyword arguments act like the :vim:`:highlight` command's
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
        args[0:0] = ['clear']
        return commands.highlight(*args)

    if disable:
        args.append('NONE')
        return commands.highlight(*args)

    if default:
        args.append('default')

    for name, value in kwargs.items():
        args.append(f'{name}={value}')

    ret = commands.highlight(*args)
    return ret


def _convert_colour_names(kwargs):
    _cterm_argnames = set(('ctermfg', 'ctermbg', 'ctermul'))
    _gui_argnames = set(('guifg', 'guibg', 'guisp'))
    for key, name in kwargs.items():
        if name in _std_vim_colours:
            continue
        if key in _cterm_argnames:
            kwargs[key] = colors.name_to_number.get(name.lower(), name)
        elif key in _gui_argnames:
            kwargs[key] = colors.name_to_hex.get(name.lower(), name)


def error_msg(*args):
    """A print-like function that writes an error message.

    Unlike using sys.stderr directly, this does not raise a vim.error.
    """
    msg = ' '.join(str(a) for a in args)
    common.vim_command('echohl ErrorMsg')
    common.vim_command(f'echomsg {msg!r}')


def pedit(path: str, silent=True, noerrors=False):
    """Edit file in the preview window.

    :path:     The files path.
    :silent:   If true then run the :pedit command silently.
    :noerrors: If true then add '!' to suppress errors.
    """
    cmd = []
    if silent or noerrors:
        if noerrors:
            cmd.append('silent!')
        else:
            cmd.append('silent')
    cmd.extend(['pedit', path])
    common.vim_command(' '.join(cmd))


def feedkeys(keys, mode=None, literal=False):
    """Feed keys into Vim's type-ahead buffer.

    Unlike vim.feedkeys() directly this provides support for using special key
    mnemonics.

    :keys:    The keys string.
    :mode:    The mode passed to Vim's feedkeys function.
    :literal: If true then the *keys* is passed to feedkeys using single
              quotes.
    """
    if literal:
        keys = _single_quote(keys)
    else:
        keys = _double_quote(keys)
    if mode is not None:
        mode = _single_quote(mode)
        cmd = f'call feedkeys({keys}, {mode})'
    else:
        cmd = f'call feedkeys({keys})'
    print("FEED", repr(cmd))
    wrappers.vim.command(cmd)


def _single_quote(expr):
    """Put expression in single quotes, using Vim escaping rules.

    :expr: The Vim expression.
    """
    expr = expr.replace("'", "''")
    return f"'{expr}'"


def _double_quote(expr):
    """Put expression in double quotes, using Vim escaping rules.

    :expr: The Vim expression.
    """
    expr = expr.replace('"', r'\"')
    return f'"{expr}"'


def call_soon(func):
    """Arrange to call a function 'soon'.

    This uses a Vim timer with a delay of 0ms to schedule the function call.
    This means that currently executing Python code will complete *before*
    the function is invoked.

    :func: The function to be invoked. It takes no arguments.
    """
    def do_call(_):
        func()
    Timer(0, do_call)


def timer_stopall():
    """Convenience function that invokes `Timer.stop_all`."""
    Timer.stop_all()


def popup_clear(force=False):
    """Convenience function that invokes `Popup.clear`."""
    Popup.clear(force)


def find_buffer_by_name(name: str) -> Optional[wrappers.Buffer]:
    """Find the buffer with a given name.

    The name must be an exact match.

    :name: The name of the buffer to find.
    """
    for buf in wrappers.vim.buffers:
        if buf.name == name:
            return buf
    return None


class saved_winview:
    """Context manager that saves and restores the current window's view."""
    view: dict

    def __enter__(self):
        self.view = wrappers.vim.winsaveview()

    def __exit__(self, *args, **kwargs):
        wrappers.vim.winrestview(self.view)


def log_status():
    """Dump useful diagnostic information to the VPE log.

    The output is intended for things like diagnosing issues with VPE or to
    help plug-in development. The details of the output may change
    significantly between VPE releases.
    """
    # pylint: disable=protected-access
    log(f'{len(Timer._timers)=}')
    log(f'{len(Popup._popups)=}')
    log(f'{len(Callback.callbacks)=}')
    log(f'{len(Timer._timers)=}')


def _setup_keys():
    _special_key_names = (
        'Up', 'Down', 'Left', 'Right', 'Help', 'Undo', 'Insert', 'Home', 'End',
        'PageUp', 'PageDown', 'kHome', 'kEnd', 'kPageUp', 'kPageDown', 'kPlus',
        'kMinus', 'kMultiply', 'kDivide', 'kEnter', 'kPoint', 'LeftMouse',
        'LeftDrag', 'LeftRelease', 'MiddleMouse', 'MiddleDrag',
        'MiddleRelease', 'RightMouse', 'RightDrag', 'RightRelease', 'X1Mouse',
        'X1Drag', 'X1Release', 'X2Mouse', 'X2Drag', 'X2Release',
        'ScrollWheelUp', 'ScrollWheelDown',
    )

    def register_key(name, unmodified=True, modifiers='SCMA'):
        if unmodified:
            key_name = f'<{name}>'
            common.vim_command(rf'let g:_vpe_temp_ = "\{key_name}"')
            _special_keymap[wrappers.vim.vars['_vpe_temp_']] = key_name
        for m in modifiers:
            key_name = f'<{m}-{name}>'
            common.vim_command(rf'let g:_vpe_temp_ = "\{key_name}"')
            _special_keymap[wrappers.vim.vars['_vpe_temp_']] = key_name

    for k in _special_key_names:
        register_key(k)
    for n in range(12):
        register_key(f'F{n + 1}')
    for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        register_key(c, unmodified=False, modifiers='CMA')


log: Log = Log('VPE-log')
_setup_keys()
del _setup_keys
