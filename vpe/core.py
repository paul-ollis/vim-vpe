"""Enhanced module for using Python3 in Vim.

This provides the Vim class, which is a wrapper around Vim's built-in *vim*
module. It is intended that a Vim instance can be uses as a replacement for the
*vim* module. For example:<py>:

    from vpe import vim
    # Now use 'vim' as an extended version of the ``vim`` module.
    # ...
"""
# pylint: disable=too-many-lines

import collections
import inspect
import io
import platform
import string
import sys
import time
import weakref
from functools import partial
from typing import Callable, List, Optional, Tuple, Type, Union

import vim as _vim

import vpe
from . import colors, common, wrappers

__api__ = [
    'expr_arg',
]
__shadow_api__ = [
    '_VimDesc',
]
__all__ = [
    'AutoCmdGroup', 'Popup', 'PopupAtCursor', 'PopupBeval',
    'PopupNotification', 'PopupDialog', 'PopupMenu', 'ScratchBuffer',
    'Log', 'error_msg', 'warning_msg', 'echo_msg', 'log',
    'saved_winview', 'highlight', 'pedit', 'popup_clear',
    'timer_stopall', 'find_buffer_by_name', 'feedkeys', 'get_display_buffer',
    'define_command', 'temp_active_window', 'CommandHandler',
    'EventHandler', 'BufEventHandler', 'temp_active_buffer',
    'saved_current_window',
    'expr_arg',
]

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

#: Dictionary mapping from byte sequences to symbolic names for keys.
#:
#: Most entries are automatically generated, but some need to be entered
#: manually.
_special_keymap: dict = {
    b'\x80\xfdd': '<Mouse>',
}

_VIM_FUNC_DEFS = """
function! VPE_Call(uid, func_name, ...)
    let g:_vpe_args_ = {}
    let g:_vpe_args_['uid'] = a:uid
    let g:_vpe_args_['args'] = a:000
    try
        return py3eval('vpe.Callback.invoke()')
    catch
        py3 << EOF
import vim as _vim
print(f'VPE_Call failed: {_vim.vvars["exception"]}')
EOF
    finally
        " Without this a circular reference seem to 'escape', which can
        " cause Vim to accumulate memory while it is inactive and timers are
        " regularly firing (an artifact of when Vim permits its garbage
        " collector to run).
        if has_key(g:_vpe_args_, 'args')
            unlet g:_vpe_args_['args']
        endif
    endtry
endfunction

function! VPE_CmdCall(uid, func_name, line1, line2, range, count, bang, mods, reg, ...)
    let g:_vpe_args_ = {}
    let g:_vpe_args_['uid'] = a:uid
    let g:_vpe_args_['line1'] = a:line1
    let g:_vpe_args_['line2'] = a:line2
    let g:_vpe_args_['range'] = a:range
    let g:_vpe_args_['count'] = a:count
    let g:_vpe_args_['bang'] = a:bang
    let g:_vpe_args_['mods'] = a:mods
    let g:_vpe_args_['reg'] = a:reg
    let g:_vpe_args_['args'] = a:000
    try
        return py3eval('vpe.Callback.invoke()')
    catch
        py3 << EOF
import vim as _vim
print(f'VPE_CmdCall failed: {_vim.vvars["exception"]}')
EOF
    endtry
endfunction
"""
_vim.command(_VIM_FUNC_DEFS)


def _clean_ident(s):
    """Clean up a string so it is a valid Vim identifier.

    The returned value can be used in group names.
    """
    valid_chars = set(string.ascii_letters + string.digits)
    def fold_to_ident_char(c):
        if c not in valid_chars:
            return 'x'                                       # pragma: no cover
        return c
    ident = ''.join(fold_to_ident_char(c) for c in s)
    if ident != s:
        return ident
    return s                                                 # pragma: no cover


class ScratchBuffer(wrappers.Buffer):
    """A scratch buffer.

    A scratch buffer has no associated file, has no swap file, never gets
    written and never appears to be modified. The content of such a buffer is
    typically under the control of plugin code. Direct editing is disabled.

    Direct instantiation is not recommended; use `get_display_buffer`, which
    creates bufferes with suitably formatted names.

    :name:         The name for the buffer.
    :buffer:       The :vim:`python-buffer` that this wraps.
    :@simple_name:
        An alternative simple name. This is used in the generation of the
        `syntax_prefix` and `auto_grp_name` property values. If this is not set
        then is is the same a the *name* parameter. If this is not a valid
        identifier then it is converted to one by replacing invalid characters
        with 'x'.
    """
    def __init__(self, name, buffer, simple_name=None):
        super().__init__(buffer)
        self.__dict__['_base_name'] = name
        self.__dict__['simple_name'] = _clean_ident(simple_name or name)
        self.set_ext_name('')
        with AutoCmdGroup(self.auto_grp_name) as grp:
            grp.add('BufWinEnter', self.on_first_showing, pat=self, once=True)

        options = self.options
        options.buftype = 'nofile'
        options.swapfile = False
        options.modified = False
        options.readonly = True
        options.modifiable = False
        options.bufhidden = 'hide'
        options.buflisted = True

        # Allow subclasses a chance to set addidtional option or over-ride the
        # above settings.
        common.call_soon(self.init_options)

    def init_options(self):
        """Initialise the scratch buffer specific options.

        This gets invoked via call_soon because option setting can otherwise
        silently fail for subclasses.

        Subclasses may over-ride this.
        """

    @property
    def syntax_prefix(self):
        """A suitable prefix for syntax items in this buffer."""
        return f'Syn_{self.simple_name}_'

    @property
    def auto_grp_name(self):
        """A suitable name for auto commands for this buffer."""
        return f'Grp{self.simple_name}'

    def set_ext_name(self, name):
        """Set the extension name for this buffer.

        :name: The extension part of the name
        """
        if name:
            if platform.system() == 'Windows':       # pragma: no cover windows
                self.name = rf'{self._base_name}\{name}'
            else:
                self.name = f'{self._base_name}/{name}'
        else:
            self.name = self._base_name

    def show(self, *, splitlines: int = 0, splitcols: int = 0) -> bool:
        """Make this buffer visible.

        Without a *splitlines* or *splitcols* argument, this will use the
        current window to show this buffer. Otherwise the current window is
        split, horizontally if *splitlines* != 0 or vertically if *splitcols*
        != 0. The buffer is shown in the top/left part of the split. A positive
        split specifies how many lines/columns to allocate to the bottom/right
        part of the split. A negative split specifies how many lines to
        allocate to the top/left window.

        :splitlines: Number of lines allocated to the top/bottom of the split.
        :splitcols:  Number of columns allocated to the left or right window of
                     the split.
        :return:     True if the window is successfully shown.
        """
        win = wrappers.vim.current.window
        windows = wrappers.vim.windows
        w_number = win.number
        if splitlines:
            w_height = win.height
            if w_height < 3:
                error_msg('Window is too short to split')
                return False

            wrappers.commands.wincmd('s')
            split_size = min(abs(splitlines), w_height - 2)
            rem_size = w_height - split_size - 1
            if splitlines > 0:
                windows[w_number - 1].height = rem_size
                windows[w_number].height = split_size
            else:
                windows[w_number - 1].height = split_size
                windows[w_number].height =rem_size

        elif splitcols:
            w_width = win.width
            if w_width < 3:
                error_msg('Window is too narrow to split')
                return False

            wrappers.commands.wincmd('v')
            split_size = min(abs(splitcols), w_width - 2)
            rem_size = w_width - split_size - 1
            if splitcols > 0:
                windows[w_number - 1].width = rem_size
                windows[w_number].width = split_size
            else:
                windows[w_number - 1].width = split_size
                windows[w_number].width =rem_size

        wrappers.commands.buffer(self.number, bang=True)
        return True

    def on_first_showing(self):
        """Invoked when the buffer is first, successfully displayed.

        This is expected to be extended (possibly over-ridden) by subclasses.
        """

    def modifiable(self) -> wrappers.TemporaryOptions:
        """Create a context that allows the buffer to be modified."""
        return self.temp_options(modifiable=True, readonly=False)


def get_display_buffer(
            name: str, buf_class: Type[ScratchBuffer] = ScratchBuffer
        ) -> ScratchBuffer:
    """Get a named display-only buffer.

    The actual buffer name will be of the form '/[[name]]'. The buffer is
    created if it does not already exist.

    :name: An identifying name for this buffer. This becomes the
           `ScratchBuffer.simple_name` attribute.
    """
    # pylint: disable=unsubscriptable-object
    if platform.system() == 'Windows': # pragma: no cover windows
        buf_name = rf'C:\[[{name}]]'
    else:
        buf_name = f'/[[{name}]]'
    b = _known_special_buffers.get(buf_name, None)
    if b is not None and b.valid:
        return b

    for b in wrappers.vim.buffers:
        if b.name == buf_name:
            break
    else:
        n = wrappers.vim.bufnr(buf_name, True)
        b = wrappers.vim.buffers[n]

    b = buf_class(buf_name, b, name)
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

    The output is stored in a Python FIFO structure, up to a maximum number of
    lines; the default is 500, change this with `set_maxlen`. No actual Vim
    buffer is created until required, which is when `show` is first
    invoked.:<py>:

        info.show()   # Make the log visible.

    The :mod:`vpe` module provides a predefined log, called 'VPE'. This is
    available for general use. VPE also uses it to log significant occurrences
    - mainly error conditions.

    :@name:  A name that maps to the corresponding display buffer.
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
        try:
            win_execute = wrappers.vim.win_execute
        except AttributeError:                               # pragma: no cover
            return
        if buf:
            for w in wrappers.vim.windows:
                if w.buffer.number == buf.number:
                    # TODO: Figure out why this can cause:
                    #           Vim(redraw):E315: ml_get: invalid lnum: 2
                    try:
                        win_execute(wrappers.vim.win_getid(w.number), '$')
                        win_execute(wrappers.vim.win_getid(w.number), 'redraw')
                    except _vim.error:                       # pragma: no cover
                        pass

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
                    del buf[:d]

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
            wrappers.commands.wincmd('s')
            self.buf.show()
            wrappers.commands.wincmd('w')

    def set_maxlen(self, maxlen: int) -> None:
        """Set the maximum length of the log's FIFO.

        This will discard older lines if necessary.

        :maxlen: How many lines to store in the FIFO.
        """
        if maxlen != self.fifo.maxlen:
            self.fifo = collections.deque(self.fifo, maxlen)
        self._trim()


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
    """A Pythonic way to use Vim's popup windows.

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
    properties of the same name. For example, to change the first displayed
    line:<py>:

        p = vpe.Popup(my_text)
        ...
        p.firstline += 3

    The close option must be accessed as close_control, because `close` is a
    Popup method. There is no filter or callback property.

    :content:   The content for the window.
    :p_options: Nearly all the standard popup_create options (line, col, pos
                *etc*.) can be provided as keyword arguments. The exceptions
                are filter and callback. Over ride the `on_key` and `on_close`
                methods instead.
    """
    _popups: dict = {}
    _create_func = 'popup_create'

    def __init__(self, content, **p_options):
        close_cb = common.Callback(self._on_close)
        filter_cb = common.Callback(self._on_key, pass_bytes=True)
        p_options['callback'] = close_cb.as_vim_function()
        p_options['filter'] = filter_cb.as_vim_function()
        self._id = getattr(wrappers.vim, self._create_func)(content, p_options)
        self._popups[self._id] = weakref.ref(self, self._on_del)
        self._clean_up()
        self.result = -1

    @property
    def id(self) -> int:
        """The ID of the Vim popup window."""
        return self._id

    @property
    def buffer(self) -> Optional[wrappers.Buffer]:
        """The buffer holding the window's content.

        :return:
            A `Buffer` or ``None``.
        """
        n = wrappers.vim.winbufnr(self._id)
        if n >= 0:
            return wrappers.vim.buffers[n]

        return None

    @classmethod
    def _on_del(cls, _, _win_id=None):
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

    def setoptions(self, **p_options) -> None:
        """Set a number of options at once.

        This is useful to set certain groups of options that cannot be
        separately set. For example 'textpropid' cannot be set unless
        'textprop' is set in the same popup_setoptions call.
        """
        wrappers.vim.popup_setoptions(self._id, p_options)

    def move(self, **p_options) -> None:
        """Set a number of move options at once.

        An efficient way to set multiple options that affect the popup's
        position.
        """
        wrappers.vim.popup_move(self._id, p_options)

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
        method is invoked as follows:

        - Merged key sequences are split, so that this is always invoked
          with the sequence for just a single key.
        - Anything that does not convert to a special name is decoded to a
          Python string, if possible.
        - Special key sequences are converted to the standard Vim symbolic
          names such as <Up>, <LeftMouse>, <F11>, *etc*. Modifiers are also
          handled where possible - the modified symbolic names known to be
          available are:

          - <S-Up> <S-Down> <S-Left> <S-Right> <S-Home> <S-End> <S-Insert>
          - <C-F1> <C-F2>, *etc*.
          - <C-A> <M-A> <S-M-A> <C-M-A>, <C-B> ... <C-M-Z>

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
        ret = False
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

    # TODO: Investigate why bytes are now sometimes strings.
    #       I think there has been an improvement in Vim that converts bytes
    #       to strings when calling Python code. This is generally better, but
    #       technically wrong for raw key handling.
    #       I am not really happy with the work-around for this.
    @staticmethod
    def _split_key_sequences(s):
        if isinstance(s, str):
            try:
                s = s.encode()
            except UnicodeError:                             # pragma: no cover
                # Really should not occur, but...
                yield s

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
    textprop = _PopupRWPos('textprop')
    textpropid = _PopupRWPos('textpropid')
    textpropwin = _PopupRWPos('textpropwin')
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


# TODO: This could probably be a more generic mechanism baked into Callback.
class AutoCmdCallback(common.Callback):
    """Thin `Callback` wrapper to support debugging."""
    # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug_meta: Optional[Tuple[str, str]] = None

    def x__call__(self, *args, **kwargs):
        """Useful for some debugging."""
        name, pat = self.debug_meta
        print(
            f'Invoke autocmd: {name} pat={pat} state={wrappers.vim.state()}'
            f' mode={wrappers.vim.mode()}'
            f' inst={self.ref_inst}'
            f' method={self.method}'
        )
        return super().__call__(*args, **kwargs)


class AutoCmdGroup:
    """A Pythonic way to define auto commands.

    This is a context manager that supports definition of autocommands that:

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
    _options_context: wrappers.TemporaryOptions

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self._options_context = wrappers.vim.temp_options(
            cpoptions=vpe.VIM_DEFAULT)
        self._options_context.activate()
        common.vim_command(f'augroup {self.name}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        common.vim_command('augroup END')
        self._options_context.restore()

    @staticmethod
    def delete_all():
        """Delete all entries in the group."""
        common.vim_command('autocmd!')

    @staticmethod
    def add(
            event, func, *, pat='<buffer>', once=False, nested=False,
            **kwargs):
        """Add a new auto command to the group.

        :event:  The name of the event.
        :func:   The Python function to invoke. Plain functions and instance
                 methods are supported.
        :pat:    The file pattern to match. If not supplied then the special
                 '<buffer>' pattern is used. If the argument is a `Buffer` then
                 the special pattern '<buffer=N> is used.
        :once:   The standard ':autocmd' options.
        :nested: The standard ':autocmd' options.
        :kwargs: Additional keyword arguments to be passed the *func*.
        """
        if isinstance(pat, wrappers.Buffer):
            pat = f'<buffer={pat.number}>'
        cmd_seq = ['autocmd', event, pat]
        if once:
            if wrappers.vim.has('patch-8.1.1113'):
                cmd_seq.append('++once')
        if nested:
            if wrappers.vim.has('patch-8.1.1113'):
                cmd_seq.append('++nested')
            else:
                cmd_seq.append('nested')
        kwargs = kwargs or None
        callback = AutoCmdCallback(func, once=once, py_kwargs=kwargs)
        cmd_seq.append(callback.as_call())
        common.vim_command(' '.join(cmd_seq))
        callback.debug_meta = event, pat


class EventHandler:
    """Mix-in to support mapping events to methods.

    This provides a convenient alternative to direct use of `AutoCmdGroup`.
    The default pattern (see :vim:`autocmd-patterns`) is '*' unless explicitly
    set by the `handle` decorator.
    """
    _default_event_pattern: Optional[str] = '*'

    def auto_define_event_handlers(self, group_name: str, delete_all=False):
        """Set up mappings for event handling methods.

        :group_name: The name for the auto command group (see :vim:`augrp`).
                     This will be converted to a valid Vim identifier.
        :delete_all: If set then all previous auto commands in the group are
                     deleted.
        """
        def is_method(obj):
            return inspect.ismethod(obj) or inspect.isfunction(obj)

        group_ident = _clean_ident(group_name)
        if group_ident in ('', '_', '__'):
            vpe.error_msg(
                f'{group_name} cannot be converted to a sensible Vim'
                ' identifier', soon=True)
            return

        with AutoCmdGroup(group_ident) as grp:
            if delete_all:
                grp.delete_all()
            for _, method in inspect.getmembers(self, is_method):
                info = getattr(method, '_eventmappings_', None)
                if info is not None:
                    for name, kwargs in info:
                        kw = kwargs.copy()
                        if 'pat' not in kw:
                            kw['pat'] = self._default_event_pattern or self
                        grp.add(name, method, **kw)

    @staticmethod
    def handle(name: str, **kwargs) -> Callable[[Callable], Callable]:
        """Decorator to make an event invoke a method.

        :name:   The name of the event (see :vim:`autocmd-events`.
        :kwargs: See `AutoCmdGroup.add` for the supported arguments.
                 Note that the ``pat`` argument defaults to '*', not
                 '<buffer>'.
        """
        def wrapper(func: Callable) -> Callable:
            info = getattr(func, '_eventmappings_', None)
            if info is None:
                setattr(func, '_eventmappings_', [])
                info = getattr(func, '_eventmappings_')
            info.append((name, kwargs))
            return func

        return wrapper


class BufEventHandler(EventHandler):
    """Mix-in to support mapping events to methods for buffers.

    This differs from EventHandler by the use of ``self`` as the default
    pattern.
    """
    _default_event_pattern = None


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
        return wrappers.commands.highlight(*args)
    if group:
        args.append(group)
    if clear:
        args[0:0] = ['clear']
        return wrappers.commands.highlight(*args)

    if disable:
        args.append('NONE')
        return wrappers.commands.highlight(*args)

    if default:
        args.append('default')

    for name, value in kwargs.items():
        args.append(f'{name}={value}')

    ret = wrappers.commands.highlight(*args)
    return ret


def _name_to_number(name):
    if isinstance(name, int):
        return name
    return colors.to_256_num(colors.well_defined_name(name))


def _convert_colour_names(kwargs):
    _cterm_argnames = set(('ctermfg', 'ctermbg', 'ctermul'))
    _gui_argnames = set(('guifg', 'guibg', 'guisp'))
    for key, name in kwargs.items():
        if name in _std_vim_colours or not isinstance(name, str):
            continue
        if key in _cterm_argnames:
            kwargs[key] = _name_to_number(name)
        elif key in _gui_argnames:
            kwargs[key] = colors.well_defined_name(name)


def _echo_msg(*args, hl='None'):
    msg = ' '.join(str(a) for a in args)
    common.vim_command(f'echohl {hl}')
    try:
        common.vim_command(f'echomsg {msg!r}')
    finally:
        common.vim_command('echohl None')


def _invoke_now_or_soon(soon, func, *args, **kwargs):
    """Invoke a function immediately or soon.

    :soon:   If false then invoke immediately. Otherwise arrange to invoke soon
             from Vim's execution loop.
    :func:   The function.
    :args:   The functions arguments.
    :kwargs: The function's keyword arguments.
    """
    if soon:
        common.call_soon(partial(func, *args, **kwargs))
    else:
        func(*args, **kwargs)


def error_msg(*args, soon=False):
    """A print-like function that writes an error message.

    Unlike using sys.stderr directly, this does not raise a vim.error.

    :args: All non-keyword arguments are converted to strings before output.
    :soon: If set, delay invocation until the back in the Vim main loop.
    """
    _invoke_now_or_soon(soon, _echo_msg, *args, hl='ErrorMsg')


def warning_msg(*args, soon=False):
    """A print-like function that writes a warning message.

    :args: All non-keyword arguments are converted to strings before output.
    :soon: If set, delay invocation until the back in the Vim main loop.
    """
    _invoke_now_or_soon(soon, _echo_msg, *args, hl='WarningMsg')


def echo_msg(*args, soon=False):
    """Like `error_msg`, but for information.

    :args: All non-keyword arguments are converted to strings before output.
    :soon: If set, delay invocation until the back in the Vim main loop.
    """
    _invoke_now_or_soon(soon, _echo_msg, *args)


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


def define_command(
        name: str, func: Callable, *, nargs: Union[int, str] = 0,
        complete: str = '', range: Union[bool, str] = '', count: str = '',
        addr: str = '', bang: bool = False, bar: bool = False,
        register: bool = False, buffer: bool = False, replace: bool = True,
        pass_info: bool = True, args=(), kwargs: Optional[dict] = None):
        # pylint: disable=too-many-locals,redefined-builtin
    """Create a user defined command that invokes a Python function.

    When the command is executed, the function is invoked as:<py>:

        func(info, *args, *cmd_args, **kwargs)

    The *info* parameter is `CommandInfo` instance which carries all the meta
    information, such as the command name, range, modifiers, *etc*. The
    *cmd_args* are those provided to the command; each a string.
    The *args* and *kwargs* are those provided to this function.

    :name:      The command name; must follow the rules for :vim:`:command`.
    :func:      The function that implements the command.
    :nargs:     The number of supported arguments; must follow the rules for
                :vim:`:command-nargs`, except that integer values of 0, 1 are
                permitted.
    :complete:  Argument completion mode (see :vim:`command-complete`). Does
                not currently support 'custom' or 'customlist'.
    :range:     The permitted type of range; must follow the rules for
                :vim:`:command-range`, except that the N value may be an
                integer.
    :count:     The permitted type of count; must follow the rules for
                :vim:`:command-count`, except that the N value may be an
                integer. Use count=0 to get the same behaviour as '-count'.
    :addr:      How range or count values are interpreted
                (see :vim:`:command-addr`).
    :bang:      If set then the '!' modifieer is supported (see
                :vim:`:command-bang`).
    :bar:       If set then the command may be followed by a '|' (see
                :vim:`:command-bar`).
    :register:  If set then an optional register is supported (see
                :vim:`:command-register`).
    :buffer:    If set then the command is only for the current buffer (see
                :vim:`:command-buffer`).
    :replace:   If set (the default) then 'command!' is used to replace an
                existing command of the same name.
    :pass_info: If set then the first argument passed to func is a MappingInfo
                object. Defaults to True.
    :args:      Additional arguments to pass to the mapped function.
    :kwargs:    Additional keyword arguments to pass to the mapped function.
    """
    cmd_args: List[Union[expr_arg, int]] = [
        expr_arg('<line1>'), expr_arg('<line2>'), expr_arg('<range>'),
        expr_arg('<count>'), expr_arg('<q-bang>'), expr_arg('<q-mods>'),
        expr_arg('<q-reg>'), expr_arg('<f-args>')]
    if not wrappers.vim.has('patch-8.0.1089'):
        cmd_args[2] = -1                                     # pragma: no cover
    cb = common.CommandCallback(
        func, name=name, py_args=args, py_kwargs=kwargs or {},
        vim_exprs=tuple(cmd_args), pass_info=pass_info)
    cmd = ['command' + '!' if replace else '']
    if nargs:
        cmd.append(f'-nargs={nargs}')
    if complete:
        cmd.append(f'-complete={complete}')
    if range:
        if range is True:
            cmd.append('-range')
        else:
            cmd.append(f'-range={range}')
    if count:
        cmd.append(f'-count={count}')
    if addr:
        cmd.append(f'-addr={addr}')
    if bang:
        cmd.append('-bang')
    if bar:
        cmd.append('-bar')
    if register:
        cmd.append('-register')
    if buffer:
        cmd.append('-buffer')
    cmd.append(name)
    cmd.append(cb.as_call())
    wrappers.vim.command(' '.join(cmd))


class CommandHandler:
    """Mix-in to support mapping user commands to methods."""

    def auto_define_commands(self):
        """Set up mappings for command methods."""
        def is_method(obj):
            return inspect.ismethod(obj) or inspect.isfunction(obj)

        def_cmd = partial(define_command, pass_info=False)
        with wrappers.vim.temp_options(cpoptions=vpe.VIM_DEFAULT):
            for _, method in inspect.getmembers(self, is_method):
                info = getattr(method, '_cmdmappings_', None)
                if info is not None:
                    for name, kwargs in info:
                        def_cmd(name, method, **kwargs)

    @staticmethod
    def command(name: str, **kwargs) -> Callable[[Callable], Callable]:
        """Decorator to make a user command invoke a method.

        :name:   The name of the user defined command.
        :kwargs: See `vpe.define_command` for the supported values.
        """
        def wrapper(func: Callable) -> Callable:
            info = getattr(func, '_cmdmappings_', None)
            if info is None:
                setattr(func, '_cmdmappings_', [])
                info = getattr(func, '_cmdmappings_')
            info.append((name, kwargs))
            return func

        return wrapper


def timer_stopall():
    """Convenience function that invokes `Timer.stop_all`."""
    common.Timer.stop_all()


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
    view: dict = {}

    def __enter__(self):
        self.view = wrappers.vim.winsaveview()

    def __exit__(self, *args, **kwargs):
        wrappers.vim.winrestview(self.view)


class saved_current_window:
    """Context manager that saves and restores the active window."""
    saved_win: wrappers.Window

    def __enter__(self):
        self.saved_win = wrappers.vim.current.window

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.saved_win.valid:
            if wrappers.vim.current.window.id != self.saved_win.id:
                wrappers.commands.wincmd('w', a=self.saved_win.number)


class temp_active_window(saved_current_window):
    """Context manager that temporarily changes the active window.

    :win: The `Window` to switch to.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, win: wrappers.Window):
        self.win = win

    def __enter__(self):
        super().__enter__()
        if wrappers.vim.current.window.id != self.win.id:
            wrappers.commands.wincmd('w', a=self.win.number)


class temp_active_buffer:
    """Context manager that temporarily changes the active buffer.

    If the current window is not currently showing this buffer then the window
    is switched to this buffer. When the context exits, the original buffer is
    restored. No actions occur unless necessary.

    If a switch is made then while the context is actives:

    - autocommands are disabled (by setting eventignore=all).
    - the replaced buffer has bufhidden=hide set.
    - The alternative buffer register ('#') is not updated.

    This can be used to execute Vim operations that only apply to the current
    buffer; for example setting up syntax highlighting.

    :buf: The `Buffer` to switch to.
    """
    saved_buf: wrappers.Buffer
    buf_options_ctxt: wrappers.TemporaryOptions
    glob_options_ctxt: wrappers.TemporaryOptions
    view: dict = {}

    def __init__(self, buf: wrappers.Buffer):
        self.buf = buf
        self.no_action_required = False

    def __enter__(self):
        if wrappers.vim.current.buffer.number == self.buf.number:
            self.no_action_required = True
            return

        self.view = wrappers.vim.winsaveview()
        self.saved_buf = wrappers.vim.current.buffer
        self.buf_options_ctxt = self.saved_buf.temp_options(bufhidden='hide')
        self.glob_options_ctxt = wrappers.vim.temp_options(eventignore='all')

        self.buf_options_ctxt.activate()
        self.glob_options_ctxt.activate()
        wrappers.commands.buffer(self.buf.number)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.no_action_required:
            self.no_action_required = False
            return

        if wrappers.vim.current.buffer.number != self.saved_buf.number:
            wrappers.commands.buffer(self.saved_buf.number)
        self.buf_options_ctxt.restore()
        self.glob_options_ctxt.restore()
        wrappers.vim.winrestview(self.view)


def log_status():
    """Dump useful diagnostic information to the VPE log.

    The output is intended for things like diagnosing issues with VPE or to
    help plug-in development. The details of the output may change
    significantly between VPE releases.
    """
    # pylint: disable=protected-access
    log(f'Popup._popups = {len(Popup._popups)}')
    log(f'Callback.callbacks = {len(common.Callback.callbacks)}')


def _setup_keys():
    _special_key_names = (
        'Up', 'Down', 'Left', 'Right', 'Help', 'Undo', 'Insert', 'Home', 'End',
        'PageUp', 'PageDown', 'kHome', 'kEnd', 'kPageUp', 'kPageDown', 'kPlus',
        'kMinus', 'kMultiply', 'kDivide', 'kEnter', 'kPoint', 'LeftMouse',
        'LeftDrag', 'LeftRelease', 'MiddleMouse', 'MiddleDrag',
        'MiddleRelease', 'RightMouse', 'RightDrag', 'RightRelease', 'X1Mouse',
        'X1Drag', 'X1Release', 'X2Mouse', 'X2Drag', 'X2Release',
        'ScrollWheelUp', 'ScrollWheelDown', 'Mouse',
    )

    def register_key(name, unmodified=True, modifiers='SCM'):
        if unmodified:
            key_name = f'<{name}>'
            common.vim_command(rf'let g:_vpe_temp_ = "\{key_name}"')
            _special_keymap[wrappers.vim.vars['_vpe_temp_']] = key_name
        for m in modifiers:
            sym_name = key_name = f'<{m}-{name}>'
            if len(name) == 1:
                sym_name = f'<{m}-{name.upper()}>'
            common.vim_command(rf'let g:_vpe_temp_ = "\{key_name}"')
            _special_keymap[wrappers.vim.vars['_vpe_temp_']] = sym_name

    for k in _special_key_names:
        register_key(k)
    for n in range(12):
        register_key(f'F{n + 1}')
    letters = 'abcdefghijklmnopqrstuvwxyz'
    modifiers = ('C', 'M', 'C-M', 'S-M')
    for c in letters:
        register_key(c, unmodified=False, modifiers=modifiers)


log: Log = Log('VPE-log')
_setup_keys()
del _setup_keys
