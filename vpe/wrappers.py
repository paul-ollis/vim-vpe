"""Wrappers around the built-in Vim Python types.

You should not normally need to import this module directly.
"""
# pylint: disable=too-many-lines

import collections
import itertools
import pathlib
import pprint
import weakref
from typing import (
    Any, Callable, ClassVar, Dict, Iterator, List, Optional, Set, Tuple, Type,
    Union)

import vim as _vim

from . import common

__all__ = ('tabpages', 'TabPage', 'Vim', 'Registers', 'vim',
           'Function', 'windows', 'Window',
           'buffers', 'Buffer', 'Range', 'Struct', 'VI_DEFAULT', 'VI_DEFAULT')
__api__ = ('Commands', 'Command')

# Type aliases
ListenerCallbackFunc = Callable[[int, int, int, int, List[Dict]], None]
ListenerCallbackMethod = Callable[[int, int, int, List[Dict]], None]

# Special values used to reset represent Vi or Vim default values. Currently
# only use to set options.
VI_DEFAULT =  object()
VIM_DEFAULT =  object()

_blockedVimCommands = set((
    "function",
    "endfunction",
    "if",
    "else",
    "elseif",
    "endif",
    "while",
    "endwhile",
    "continue",
    "break",
    "try",
    "endtry",
    "catch",
    "finally",
    "throw",
    "silent",
))
_blockedVimFunctions = set((
    "libcall",
    "libcallnr",
))
_position_name_to_flag = {
    'after': '.',
    'before': '-',
    'first': '0',
    'last': '$'
}
_comma_options = set((
    "belloff", "bo",
    "cdpath", "cd",
    "completepopup", "cpp",
    "isfname", "isf",
    "isident", "isi",
    "iskeyword", "isk",
    "isprint", "isp",
    "path", "pa",
    "previewpopup", "pvp",
    "varsofttabstop", "vsts",
    "vartabstop", "vts",
))
_single_comma_options = set((
    "backspace", "bs",
    "backupcopy", "bkc",
    "backupdir", "bdir",
    "backupskip", "bsk",
    "breakindentopt", "briopt",
    "casemap", "cmp",
    "cinkeys", "cink",
    "cinoptions", "cino",
    "cinwords", "cinw",
    "clipboard", "cb",
    "colorcolumn", "cc",
    "comments", "com",
    "complete", "cpt",
    "completeopt", "cot",
    "cscopequickfix", "csqf",
    "cursorlineopt", "culopt",
    "dictionary", "dict",
    "diffopt", "dip",
    "directory", "dir",
    "display", "dy",
    "errorformat", "efm",
    "eventignore", "ei",
    "fileencodings", "fencs",
    "fileformats", "ffs",
    "fillchars", "fcs",
    "foldclose", "fcl",
    "foldmarker", "fmr",
    "foldopen", "fdo",
    "grepformat", "gfm",
    "guicursor", "gcr",
    "guifont", "gfn",
    "guifontset", "gfs",
    "guifontwide", "gfw",
    "helplang", "hlg",
    "highlight", "hl",
    "indentkeys", "indk",
    "keymodel", "km",
    "langmap", "lmap",
    "lispwords", "lw",
    "listchars", "lcs",
    "matchpairs", "mps",
    "mouseshape", "mouses",
    "nrformats", "nf",
    "packpath", "pp",
    "printoptions", "popt",
    "renderoptions", "rop",
    "runtimepath", "rtp",
    "scrollopt", "sbo",
    "selectmode", "slm",
    "sessionoptions", "ssop",
    "spellfile", "spf",
    "spelllang", "spl",
    "spellsuggest", "sps",
    "suffixes", "su",
    "suffixesadd", "sua",
    "switchbuf", "swb",
    "tags", "tag",
    "thesaurus", "tsr",
    "toolbar", "tb",
    "undodir", "udir",
    "viewoptions", "vop",
    "viminfo", "vi",
    "viminfofile", "vif",
    "virtualedit", "ve",
    "whichwrap", "ww",
    "wildignore", "wig",
    "wildmode", "wim",
    "wildoptions", "wop",
))
_flag_options = set((
    "breakat", "brk",
    "cpoptions", "cpo",
    "formatoptions", "fo",
    "guioptions", "go",
    "mouse",
    "shortmess", "shm",
    "whichwrap", "ww",
))


class Struct:
    """A basic data storage structure.

    This is intended to store arbitrary name, value pairs as attributes.
    Attempting to read an undefined attribute gives ``None``.

    This is provided primarily to support the `Buffer.store` mechanism. Direct
    use of this class is not intended as part of the API.
    """
    def __getattr__(self, name: str):
        return self.__dict__.get(name)

    def __setattr__(self, name: str, value: Any):
        # This exists to let checkers, like MyPy, accept arbitrary attribute
        # assignment.
        self.__dict__[name] = value

    def __getstate__(self):
        """Support pickling - only intended for testing."""
        return self.__dict__

    def __setstate__(self, state):
        """Support pickling - only intended for testing."""
        self.__dict__.update(state)


class TemporaryOptions:
    """Context manager that allows options to be temporarily modified

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    This may also be used for a more manual way to save, modify and restore
    option values, using `activate` and `restore`. This is typically used by
    other context managers.

    :options: The options object.
    :presets: Keyword arguments use to preset option values to be set while the
              context is active.
    """
    def __init__(self, vim_options, **presets):
        self.__dict__.update({
            '_options': vim_options,
            '_saved': {},
            '_presets': presets,
        })

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()

    def __getattr__(self, name):
        return self._options[name]

    def __getitem__(self, name):
        return self._options[name]

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def __setitem__(self, name, value):
        if name not in self._saved:
            self._saved[name] = self._options[name]
        self._options.__setattr__(name, value)

    def activate(self):
        """Activate the temporary option changes.

        This is normally invoked automatically when the context is entered.
        However, other context managers invoke this directly.
        """
        self._saved.clear()
        for name, value in self._presets.items():
            self.__setitem__(name, value)

    def restore(self):
        """Restore backed up options to their original values.

        This is normally invoked automatically when the context is exited.
        However, other context managers invoke this directly.
        """
        for name, value in self._saved.items():
            self._options[name] = value

    def save(self, *names):
        """Explicitly back up a number of options.

        This is useful when, for example, auto commands might update options
        that you want to restore when the context exits. Only options not
        already backup by the context manager are saved.

        :names: The options to save.
        """
        for name in names:
            if name not in self._saved:
                self._saved[name] = self._options[name]


class BufferListContext(list):
    """Context manager providing a temporary list of a buffer's lines."""
    def __init__(self, vim_buffer):
        super().__init__(vim_buffer)
        self._vim_buffer = weakref.ref(vim_buffer)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        b = self._vim_buffer()
        if exc_type is None and b is not None:
            with b.temp_options(modifiable=True, readonly=False):
                b[:] = self


class Range(common.MutableSequenceProxy):
    """Wrapper around the built-in vim.Range type.

    User code should not directly instantiate this class.
    """
    # pylint: disable=too-few-public-methods

    def append(self, line_or_lines, nr=None):
        """Append one or more lines to the range.

        This is the same as using the append method of :vim:`python-range`.

        :line_or_lines: The line or lines to append.
        :nr:            If present then append after this line number.
        """
        if nr is None:
            self._proxied.append(line_or_lines)
        else:
            self._proxied.append(line_or_lines, nr)


class Buffer(common.MutableSequenceProxy):
    """Wrapper around a :vim:`python-buffer`.

    The official documentation is provided by _BufferDesc.
    """
    _known: Dict[int, "Buffer"] = {}
    _writeable = set(('name',))

    def __init__(self, buffer):
        self.__dict__['_number'] = buffer.number
        self.__dict__['_store'] = collections.defaultdict(Struct)
        self._known[buffer.number] = self
        super().__init__()

    @property
    def number(self):
        """The number of this buffer."""
        return self._number

    def store(self, key: Any) -> Struct:
        """Return a `Struct` for a give key.

        This provides a mechanism to store arbitrary data associated with a
        given buffer. A new `Struct` is created the first time a given key is
        used. An example of how this can be used:<py>:

            vim.current.buffer.store['my-store'].processed = True
            ...
            for buf in vim.buffers:
                if buf.store['my-store'].processed:
                    # Treat already processed buffers differently.
                    ...

        The :mod:`vpe` package arranges to return the same `Buffer` instance
        for a given :vim:`python-buffer` so this effectively allows you to
        associated meta-data with individual Vim buffers.
        """
        return self._store[key]

    def range(self, a: int, b: int) -> Range:
        """Get a `Range` for the buffer.

        This is like getting a :vim:`python-range` object, except that it is
        wrapped in a `Range` instance.

        :a: The start index of the range.
        :b: The end index of the range. Note that this line is included in
            the range; *i.e.* the range is inclusive, unlike Python ranges.
        """
        return self._wrap_or_decode(self._proxied.range(a, b))

    def __iter__(self):
        return iter(self._proxied)

    @classmethod
    def get_known(cls, buffer: Any) -> Optional["Buffer"]:
        """Get the Buffer instance for a given vim.buffer.

        This is only intended for internal use.

        :buffer: A standard :vim:`python-buffer`.
        """
        return cls._known.get(buffer.number)

    @property
    def valid(self) -> bool:
        """Test of this buffer is valid.

        A buffer can become invalid if, for example, the underlying Vim buffer
        has been wiped out.
        """
        try:
            return self._proxied.valid
        except KeyError:
            return False

    @property
    def vars(self) -> "Variables":
        """The buffar vars wrapped as a `Variables` instance."""
        return Variables(self._proxied.vars)

    @property
    def type(self) -> str:
        """The type name of this buffer.

        This is similar to the :vim:`'buftype'` option, but normal buffers
        have the type 'normal'.
        """
        typename = self.options.buftype
        if typename:
            return typename
        return 'normal'

    @property
    def location(self) -> str:
        """The location of the file loaded in this buffer.

        :return:
            If the buffer is not associated with a file then an empty string.
            Otherwise the absolute directory part of the file's name.
        """
        if self.name and self.type in ('normal', 'help', 'acwrite'):
            return str(pathlib.Path(self.name).parent)
        return ''

    @property
    def long_display_name(self) -> str:
        """A long-form name for display purposes."""
        if self.type == 'quickfix':
            title = vim.getqflist({'title': 1})['title']
            return f'[quickfix]: {title}'
        if self.name:
            return self.name
        return '[No name]'

    @property
    def short_display_name(self) -> str:
        """A short-form name for display purposes."""
        if self.type in ('terminal', 'popup'):
            return f'[{self.type}]'
        if self.name:
            return pathlib.Path(self.name).name
        return '[No name]'

    @property
    def short_description(self) -> str:
        """A short description for the buffer.

        :return:
            For a quickfix window this is the title string. For a terminal this
            is the buffer's name. For other types that are associated with a
            file the `location` property is provided.
        """
        if self.type == 'quickfix':
            return vim.getqflist({'title': 1})['title']
        if self.type == 'terminal':
            return self.name
        return self.location

    def is_active(self):
        """Test whether the current window is showing this buffer."""
        return vim.current.buffer is self

    def append(self, line_or_lines, nr=None):
        """Append one or more lines to the buffer.

        This is the same as using the append method of :vim:`python-buffer`.

        :line_or_lines: The line or lines to append.
        :nr:            If present then append after this line number.
        """
        if nr is None:
            self._proxied.append(line_or_lines)
        else:
            self._proxied.append(line_or_lines, nr)

    def list(self):
        """A sequence context for efficient buffer modification.

        As an example:<py>:

            with vim.current.buffer.list() as lines:
                # Now lines is a copy of the buffers lines.
                lines[2:4] = ['one']  # Update lines in-place.

            # The vim.current.buffer has now been updated with modified lines.

        Although this involves taking a copy of the buffer's lines and then
        completely replacing the buffer's set of lines, this is a much more
        efficient way to make non-trivial modifications to a buffer's contents.

        This will update the buffer, even if 'modifiable' is not set.
        """
        return BufferListContext(self)

    def temp_options(self, **presets) -> TemporaryOptions:
        """Context used to temporarily change options.

        This makes it easy, for example, to use a normally unmodifiable buffer
        to display information in a buffer. To update the displayed buffer's
        contents do something like:<py>:

            with disp_buf.temp_options(modifiable=True):
                disp.buf.append('Another line')

        When the context ends, the modifiable option is reset to its original
        value. An alterative approach is:<py>:

            with disp_buf.temp_options as opt:
                opt.modifiable = True
                disp.buf.append('Another line')

        Only options set using presets or the context object are restored when
        the context exits.

        :presets: One or more options values may be defined using keyword
                  arguments. The values are applied when the context is
                  entered.
        """
        return TemporaryOptions(self.options, **presets)

    def find_active_windows(self, all_tabpages=False) -> List['Window']:
        """Find windows where this buffer is active.

        The list windows returned is prioritised as a result of searching in
        the following order. The current window, windows in the current tab
        page, all windows in all tab pages.

        :all_tabpages: If True then all tab pages are searched. Otherwise only
                       the current tab page is searched.
        :return: A list of the windows found.
        """
        def add_win(win):
            k = win.tabpage.number, win.number
            if win.buffer is self and k not in found:
                found[k] = win

        found: Dict[int, 'Window'] = {}
        add_win(vim.current.window)
        for win in vim.current.tabpage.windows:
            add_win(win)
        if all_tabpages:
            for page in itertools.chain([vim.current.tabpage], vim.tabpages):
                for win in page.windows:
                    add_win(win)
        return list(found.values())

    def find_best_active_window(
            self, all_tabpages=False) -> Optional['Window']:
        """Find the best choice for a window where this buffer is active.

        This returns the first entry found by `find_active_windows`.

        :all_tabpages: If True (the default) all tab pages are searched.
                       Otherwise only the current tab page is searched.
        :return: The window or None.
        """
        all_windows = self.find_active_windows(all_tabpages=all_tabpages)
        return all_windows[0] if all_windows else None

    def goto_active_window(self, all_tabpages=False) -> Optional['Window']:
        """Goto the best choice window where this buffer is active.

        This goes to the first entry found by `find_active_windows`.

        :all_tabpages: If True (the default) all tab pages are searched.
                       Otherwise only the current tab page is searched.
        :return: The window that was chosen or None.
        """
        window = self.find_best_active_window(all_tabpages=all_tabpages)
        if window:
            window.goto()
        return window

    def add_listener(
            self,
            func: Union[ListenerCallbackFunc, ListenerCallbackMethod]
            ) -> common.BufListener:
        """Add a callback for changes to this buffer.

        This is implemented using :vim:`listener_add()`

        :func:
            The callback function which is invoked the following arguments:

            :buf:     The buffer that was changed. Only present if *func* is
                      not a bound method of this instance.
            :start:   Start of the range of modified lines (zero based).
            :end:     End of the range of modified lines.
            :added:   Number of lines added, negative if lines were deleted.
            :changed: A List of items with details about the changes.
        :return:
            The unique ID for this callback, as provided by
            :vim:`listener_add()`.
        """
        # TODO: Fix dependency tree.
        inst = getattr(func, '__self__', None)
        p_buf = weakref.proxy(self.buf)
        if inst is self:
            cb = common.BufListener(func, p_buf, is_method=True)
        else:
            cb = common.BufListener(func, p_buf, is_method=False)
        cb.listen_id = vim.listener_add(cb.as_vim_function(), self.number)
        return cb

    def __getattr__(self, name):
        """Make the values from getbufinfo() available as attributes.

        This extends the base class implementation.
        """
        try:
            return super().__getattr__(name)
        except AttributeError as e:
            info = vim.getbufinfo(self.number)[0]
            try:
                return info[name]
            except KeyError:
                raise e                    # pylint: disable=raise-missing-from

    @property
    def _proxied(self):
        return _vim.buffers[self.number]


class Buffers(common.ImmutableSequenceProxy):
    """Wrapper around the built-in vim.buffers.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.
    """
    # pylint: disable=too-few-public-methods
    @property
    def _proxied(self):
        return _vim.buffers


class Window(common.Proxy):
    """Wrapper around a :vim:`python-window`.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    This is a proxy that extends the vim.Window behaviour in various ways.

    @id: This is the window's unique ID (as obtained by :vim:`win_getid`).
    """
    _writeable = set(('cursor', 'width', 'height'))

    def __init__(self, window):
        super().__init__()
        n_win, n_tab = window.number, window.tabpage.number
        self.__dict__['id'] = vim.win_getid(n_win, n_tab)

    @property
    def vars(self) -> "Variables":
        """The buffar vars wrapped as a `Variables` instance."""
        return Variables(self._proxied.vars)

    def temp_options(self, **presets) -> TemporaryOptions:
        """Context used to temporarily change options.

        This does for a window what `Buffer.temp_options` does for buffer.
        """
        return TemporaryOptions(self.options, **presets)

    def goto(self) -> bool:
        """Switch to this window, if possible.

        :return: True if the current window was set successfully.
        """
        return bool(vim.win_gotoid(self.id))

    def close(self) -> bool:
        """Close this window, if possible.

        :return: True if the window was closed.
        """
        if len(self.tabpage.windows) > 1:
            commands.close(a=self.number)
            return True
        return False

    @property
    def visible_line_range(self) -> Tuple[int, int]:
        """The range of buffer lines visible within this window.

        This is a Python style range.
        """
        # TODO: Make getwininfo() values Window properties.
        info = vim.getwininfo(self.id)[0]
        if 'topline' in info and 'botline' in info:
            rng = info['topline'] - 1, info['botline']
        else:                                                # pragma: no cover
            # Needed by older versions of Vim.
            wl = vim.winline()
            bl = vim.line('.')
            wh = info['height']
            topline = bl - wl
            botline = topline + wh
            rng = topline, botline
        return rng

    @property
    def _proxied(self):
        n_tab, n_win = vim.win_id2tabwin(self.id)
        if 0 in (n_win, n_tab):
            return _deadwin
        return _vim.tabpages[n_tab - 1].windows[n_win - 1]


class Windows(common.ImmutableSequenceProxy):  # pylint: disable=too-few-public-methods
    """Wrapper around the built-in vim.windows.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    :obj: A :vim:`python-windows` object.
    """


class _DeadWin:
    # pylint: disable=too-few-public-methods
    valid: ClassVar[bool] = False


class TabPage(common.Proxy):
    """Wrapper around a :vim:`python-tabpage`.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    This is a proxy that extends the vim.Window behaviour in various ways.
    """
    # pylint: disable=too-few-public-methods
    _writeable: Set[str] = set()

    @property
    def vars(self):
        """The buffar vars wrapped as a `Variables` instance."""
        return Variables(self._proxied.vars)


class TabPages(common.ImmutableSequenceProxy):
    """Wrapper around the built-in vim.tabpages.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    This is a proxy that extends the vim.TabPages behaviour in various ways.
    """
    # pylint: disable=too-few-public-methods
    @property
    def _proxied(self):
        return _vim.tabpages

    @staticmethod
    def new(*, position='after'):
        """Create a new tab page.

        :position:
            The position relative to this tab. The standard character prefixes
            for the :vim:`:tabnew` command can be used or one of the more
            readable strings:

            'after', 'before'
                Immediately after or before the current tab (same as '.', '-'),
            'first', 'last'
                As the first or last tab (same as '0', '$'),

            This defaults to 'after'.
        """
        flag = _position_name_to_flag.get(position, position)
        common.vim_command(f'{flag}tabnew')
        return vim.current.tabpage


class Current(common.Proxy):
    """Wrapper around the built-in vim.current attribute."""
    # pylint: disable=too-few-public-methods
    _writeable = set(('line', 'buffer', 'window', 'tabpage'))

    @property
    def _proxied(self):
        return _vim.current


class ImmutableVariables(common.MutableMappingProxy):
    """Read-only base wrapper around the various vim variable dictionaries.

    This extends the behaviour so that the members appear as attributes. It is
    immutable in the sense that attributes cannot be added or removed. However,
    individual entries may be modified.
    """
    # pylint: disable=too-few-public-methods
    def __getattr__(self, name):
        if name not in self._proxied:
            return None
        return self._wrap_or_decode(self._proxied[name], name)


class Variables(ImmutableVariables):
    """Wrapper around the various vim variable dictionaries.

    This allows entries to be modified.
    """
    # pylint: disable=too-few-public-methods
    def __setattr__(self, name, value):
        self._proxied[name] = self._resolve_item(value)


class VimVariables(ImmutableVariables):
    """Wrapper around the various vim variables dictionaries.

    This is necessary to allow operations such as vim.vvars.errmsg = ''. The
    vim.vvars object has locked == FIXED. So we need to set variables using the
    good old 'let' command.
    """
    # pylint: disable=too-few-public-methods
    def __setattr__(self, name, value):
        try:
            common.vim_command(f'let v:{name} = {value!r}')
        except _vim.error:
            common.vim_command('let v:errmsg = ""')
            # pylint: disable=raise-missing-from
            raise AttributeError(
                f'can\'t set attribute {name} for {self.__class__.__name__}')


class ListOption(str):
    """Extended string used for options that represent a list of value.

    This is the base class for `CommaListOption` and `CharListOption`.
    """
    _flag_style = False
    _sep: str = ''

    def __new__(cls, value, flag_style):
        if isinstance(value, str):
            inst = super().__new__(cls, value)
        else:
            inst = super().__new__(cls, value.decode())
        inst._flag_style = flag_style
        return inst

    def __iadd__(self, value: str):
        if not isinstance(value, str):
            raise TypeError(
                'List style options only support strings.')
        parts = self._split(self)
        for v in self._split(value):
            if not self._flag_style or v not in parts:
                parts.append(v)
        return self._sep.join(parts)

    def __isub__(self, value):
        if not isinstance(value, str):
            raise TypeError(
                'List style options only support strings.')
        parts = self._split(self)
        for v in self._split(value):
            if v in parts:
                parts.remove(v)
        return self._sep.join(parts)

    @staticmethod
    def _split(_s: str) -> List[str]:
        """Split the options string according to its type.

        This needs to be over-ridden in subclasses.
        """
        return []  # pragma: no cover


class CommaListOption(ListOption):
    """Extended string used for single comma style options.

    This supports the '+=' and '-=' operations.
    """
    _sep = ','

    @staticmethod
    def _split(s):
        if s == '':
            return []
        return s.split(',')


class CharListOption(ListOption):
    """Extended string used for character list options.

    This supports the '+=' and '-=' operations.
    """
    _sep = ''

    @staticmethod
    def _split(s):
        return list(s)


class Options(ImmutableVariables):
    """Wrapper for buffer.options, *etc.*

    This extends the behaviour so that options appear as attributes. The
    standard dictionary style access still works.
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, vim_options):
        super().__init__(None)
        self.__dict__['_proxied'] = vim_options

    def __setattr__(self, name, value):
        if name not in self._proxied:
            raise AttributeError(
                f'{self.__class__.__name__} object has no attribute {name!r}')
        self._proxied[name] = self._resolve_item(value)

    def _wrap_or_decode(self, value, name=None):
        if name in _comma_options or name in _single_comma_options:
            return CommaListOption(value, flag_style=name in _flag_options)
        if name in _flag_options:
            return CharListOption(value, flag_style=True)
        if isinstance(value, bytes):
            return value.decode()
        return super()._wrap_or_decode(value)


class GlobalOptions(Options):
    """Wrapper for vim.options, *etc.*

    This extends the behaviour so that options appear as attributes. The
    standard dictionary style access still works.
    """
    _doc_names = set(('__name__', '__qualname__'))

    def __getattr__(self, name):
        oname = self.__class__.__name__
        if name in self._doc_names:
            raise AttributeError(
                f'{oname} object has no attribute {name!r}')

        v = super().__getattr__(name)
        if v is None:
            # This may be a global-local option, which cannot be accessed using
            # the standard vim.options.
            oname_form = f'+{name}'
            if common.vim_simple_eval(f'exists({oname_form!r})') == '0':
                raise AttributeError(
                    f'{oname} object has no attribute {name!r}')
        if v is not None:
            return v
        return self._wrap_or_decode(common.vim_eval(f'&g:{name}'), name)

    def __setattr__(self, name, value):
        if value is VI_DEFAULT:
            common.vim_command(f'set {name}&vi')
            return
        if value is VIM_DEFAULT:
            common.vim_command(f'set {name}&vim')
            return

        try:
            super().__setattr__(name, value)
            return
        except AttributeError as e:
            oname_form = f'+{name}'
            if common.vim_simple_eval(f'exists({oname_form!r})') == '0':
                raise e

        # This may be a global-local option, which cannot be accessed using
        # the standard vim.options.
        v = int(value) if isinstance(value, bool) else value
        v_expr = repr(v)
        if v_expr[0] == "'":
            # Convert single quoted string expression to double quoted form.
            s = v_expr[1:-1]
            s = s.replace('"', r'\"')
            s = s.replace(r"\'", "'")
            v_expr = '"' + s + '"'
        common.vim_command(f'let &g:{name} = {v_expr}')


class Registers:
    """Dictionary like access to the Vim registers.

    This allows Vim's registers to be read and modified. This is typically via
    the `Vim.registers` attribute.:<py>:

        vim.registers['a'] = 'A line of text'
        prev_copy = vim.registers[1]

    This uses :vim:`eval' to read registers and :vim:`setreg` to write them.
    Keys are converted to strings before performing the register lookup. When
    the key is the special '=' value, the un-evaluated contents of the register
    is returned.
    """
    def __getitem__(self, reg_name: Union[str, int]) -> Any:
        """Allow reading registers as dictionary entries.

        The reg_name may also be an integer value in the range 0-9.
        """
        return common.vim_simple_eval(f'@{reg_name}')

    def __setitem__(self, reg_name: Union[str, int], value: Any):
        """Allow setting registers as dictionary entries.

        The reg_name may also be an integer value in the range 0-9.
        """
        vim.setreg(f'{reg_name}', value)


class Command:
    """Wrapper to invoke a Vim command as a function.

    The `Commands` creates instances of this; direct instantiation by users is
    not intended.

    Invocation takes the form of::

        func(arg[, arg[, arg...]], [bang=<flag>], [a=<start>], [b=<end>],
             [modifiers])
        func(arg[, arg[, arg...]], [bang=<flag>], [lrange=<range>],
             [modifiers])

    The command is invoked with the arguments separated by spaces. Each
    argument is formatted as by repr(). If the *bang* keyword argument is true
    then a '!' is appended to the command. A range of lines may be set using
    the *a* and *b* arguments or *lrange*. The *a* and *b* arguments are used
    in preference to the lrange argument. If only *b* is supplied then *a* is
    set to '.' (the current line). Additional *modifiers* keyword arguments,
    such as 'vertical' are also supported; see details below.

    The *a* and *b* values may be strings or numbers. The *lrange*
    argument may be a string (*e.g.* '2,7',a vim.Range object, a standard
    Python range object or a tuple.

    :args:       All non-keyword arguments form plain arguments to the command.
    :bang:       If set then append '!' to the command.
    :lrange:     This may be a 2-tuple/list (specifying to (a, b)), a Python
                 range object (specifying range(a - 1, b)) or a simple string
                 range 'a,b'. This argument is ignored if either *a* or *b* is
                 provided.
    :a:          The start line.
    :b:          The end line (forming a range with *a*).
    :vertical:   Run with the vertical command modifier.
    :aboveleft:  Run with the aboveleft command modifier.
    :belowright: Run with the belowright command modifier.
    :topleft:    Run with the topleft command modifier.
    :botright:   Run with the botright command modifier.
    :keepalt:    Run with the keepalt command modifier. Default = True.
    :preview:    For debugging. Do not execute the command, but return what
                 would be passed to vim.command.
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, name):
        self.name = name

    def __call__(                             # pylint: disable=too-many-locals
            self, *args, bang=False, lrange='', a='', b='', preview=False,
            keepalt=True, **kwargs):
        exclamation = '!' if bang else ''
        cmd = f'{self.name}{exclamation}'
        arg_expr = ''
        if args:
            arg_expr = ' ' + ' '.join(f'{arg}' for arg in args)
        range_expr = ''
        if not (a or b):
            if lrange:
                try:
                    range_expr = f'{lrange.start + 1},{lrange.stop} '
                except AttributeError:
                    if isinstance(lrange, (list, tuple)):
                        range_expr = f'{lrange[0]},{lrange[1]} '
                    else:
                        range_expr = f'{lrange} '
        else:
            if a and b:
                range_expr = f'{a},{b} '
            elif a:
                range_expr = f'{a} '
            else:
                range_expr = f'.,{b} '
        mod_args = {'keepalt': keepalt}
        mod_args.update(kwargs)
        modifiers = (
            'vertical', 'aboveleft', 'belowright', 'topleft', 'botright',
            'keepalt')
        cmd_mods = " ".join(mod for mod in modifiers if mod_args.get(mod))
        if cmd_mods:
            cmd = f'{cmd_mods} {range_expr}{cmd}{arg_expr}'
        else:
            cmd = f'{range_expr}{cmd}{arg_expr}'
        if not preview:
            common.vim_command(cmd)
        return cmd


class Commands:
    """A namespace for the set of Vim commands.

    A single instance of this class is made available as `vpe.commands`.

    This class provides functions for a majority of Vim's commands, often
    providing a cleaner mechanism compared to :vim:`python-command`. For
    example:<py>:

        from vpe import commands
        commands.edit('README.txt')       # Start editing README.txt
        commands.print(a=10, b=20)        # Print lines 1 to 20
        commands.print(lrange=(10, 20))   # Print lines 1 to 20
        commands.write(bang=True)         # Same as :w!
        commands.split(vertical=True)     # Split current window vertically

    Each command function is actually an instance of the `Command` class. See
    its description for details of the arguments.

    Most commands that can be entered at the colon prompt are supported.
    Structural parts of vim-script (such as function, while, try, *etc*) are
    excluded.

    The vpe, vpe.mapping and vpe.syntax modules provides some functions and
    classes provide alternatives for some commands. You are encouraged to use
    these alternatives in preference to the equivalent functions provided here.
    The following is a summary of the alternatives.

    `vpe.AutoCmdGroup`
        A replacement for augroup and autocmd.

    `vpe.highlight`
        Provides keyword style arguments. See also the `vpe.syntax` module.
    `vpe.error_msg`
        Writes a message with error highlightling, but does not raise a
        vim.error.
    `vpe.mapping`
        This provides functions to make key mappings that are handled by Python
        functions.
    `vpe.syntax`
        Provides a set of classes, functions and context managers to help
        define syntax highlighting.

    See also: `vpe.pedit`.
    """
    # pylint: disable=too-few-public-methods

    def __getattr__(self, name: str) -> Command:
        if name.startswith('__'):
            raise AttributeError(
                f'No command function called {name!r} available')

        cname_form = f':{name}'
        if common.vim_simple_eval(f'exists({cname_form!r})') == '2':
            if name not in _blockedVimCommands:
                return Command(name)

        raise AttributeError(
            f'No command function called {name!r} available')


class Vim:
    """A wrapper around and replacement for the *vim* module.

    This is a instance object not a module, but it provides a API that is
    extremely compatible with the :vim:`python-vim` module. Details of the API
    are provided by _VimDesc.
    """
    _registers: ClassVar[Registers] = Registers()

    def __new__(cls, *args, **kwargs):
        """Ensure only a single Vim instance ever exists.

        This means that code like:<py>:

            myvim = vpe.Vim()

        Will result in the same object as `vpe.vim`.
        """
        try:
            cls._myself
        except AttributeError:
            cls._myself = super().__new__(cls, *args, **kwargs)
        return cls._myself

    def temp_options(self, **presets) -> TemporaryOptions:
        """Context used to temporarily change options."""
        return TemporaryOptions(self.options, **presets)

    @property
    def registers(self) -> Registers:
        """Dictionary like access to Vim's registers.

        This returns a `Registers` object.
        """
        return self._registers

    @staticmethod
    def vim():
        """Get the underlying built-in vim module."""
        return _vim

    @property
    def error(self) -> Type[_vim.error]:
        """The plain built-in Vim exception (:vim:`python-error`)."""
        return _vim.error

    @staticmethod
    def iter_all_windows() -> Iterator[Tuple[TabPage, Window]]:
        """Iterate over all the windows in all tabs.

        :yield: A tuple of TagPage and Window.
        """
        for tab in vim.tabpages:
            for win in tab.windows:
                yield tab, win

    @staticmethod
    def _vim_singletons():
        return {
            'buffers': buffers,
            'current': current,
            'options': options,
            'tabpages': tabpages,
            'vars': vars,
            'vvars': vvars,
            'windows': windows,
        }

    def __getattr__(self, name):
        # Some attributes map to single global objects.
        if name in self._vim_singletons():
            return self._vim_singletons()[name]

        # Use the standard Vim module member for preference. Otherwise make
        # Vim functions appear as members.
        try:
            attr = getattr(_vim, name)
        except AttributeError:
            return self._get_vim_function(name)
        else:
            return common.wrap_or_decode(attr)

    def __setattr__(self, name, value):
        raise AttributeError(
            f'can\'t set attribute {name} for {self.__class__.__name__}')

    def _get_vim_function(self, name):
        try:
            return Function(name)
        except ValueError:
            raise AttributeError(          # pylint: disable=raise-missing-from
                f'{self.__class__.__name__} object has no attribute {name!r}')


class Function(_vim.Function):
    """Wrapper around a vim.Function.

    This provides some wrapping or decoding of return types.
    """
    # pylint: disable=too-few-public-methods
    def __call__(self, *args, **kwargs):
        # print(f'Function.__call__: {self.name}'
        #       f' vim.state()={_vim.eval("state()")}')
        try:
            v = super().__call__(*args, **kwargs)  # pylint: disable=no-member
        except Exception as e:
            args_lines = pprint.pformat(args).splitlines()
            kwargs_lines = pprint.pformat(kwargs).splitlines()
            print(f'VPE: Function.__call__ failed: {e}')
            print(f'    self.name={self.name}')
            print(f'    self.args={self.args}')
            print(f'    self.self={self.self}')
            print(f'    args={args_lines[0]}')
            for line in args_lines[1:]:
                print(f'         {line}')
            print(f'    kwargs={kwargs_lines}')
            for line in kwargs_lines[1:]:
                print(f'         {line}')
            print(f'    vim.state()={_vim.eval("state()")}')
            raise
        if isinstance(v, bytes):
            try:
                return v.decode()
            except UnicodeError:                             # pragma: no cover
                return v
        return common.wrap_or_decode(v)


def _get_wrapped_buffer(vim_buffer: _vim.Buffer) -> Buffer:
    """Get a wrapped version of a vim buffer object.

    This always returns the same `Buffer` for a given vim buffer number.

    :vim_buffer: A buffer object as, for example vim.current.buffer.
    """
    b = Buffer.get_known(vim_buffer)
    if b is None:
        b = Buffer(vim_buffer)
    return b


common.register_wrapper(type(_vim.options), Options)
common.register_wrapper(type(_vim.windows), Windows)
common.register_wrapper(_vim.Buffer, _get_wrapped_buffer)
common.register_wrapper(_vim.Dictionary, common.MutableMappingProxy)
common.register_wrapper(_vim.Range, Range)
common.register_wrapper(_vim.TabPage, TabPage)
common.register_wrapper(_vim.Window, Window)
common.register_wrapper(_vim.List, common.MutableSequenceProxy)

options = GlobalOptions(_vim.options)
vars = Variables(_vim.vars)                 # pylint: disable=redefined-builtin
vvars = VimVariables(_vim.vvars)
buffers = Buffers()
current = Current()
tabpages = TabPages()
windows = Windows(_vim.windows)
commands = Commands()
_deadwin = _DeadWin()
vim: Vim = Vim()


# =============================================================================
# Below this point, the code merely provides shadow objects for API
# documentation.
# =============================================================================


class _VimDesc:
    """A wrapper around and replacement for the *vim* module.

    This is a instance object not a module, but it provides a API that is
    extremely compatible with the :vim:`python-vim` module.
    """
    __doc_shadow__ = 'Vim'

    @property
    def buffers(self) -> "Buffers":
        # pyre-ignore[7]:
        """A read-only container of the all the buffers."""

    @property
    def windows(self) -> 'Windows':
        # pyre-ignore[7]:
        """A read-only container of the windows of the current tab page."""

    @property
    def tabpages(self) -> "TabPages":
        # pyre-ignore[7]:
        """A read-only container of the all the tab pages."""

    @property
    def current(self) -> "Current":
        # pyre-ignore[7]:
        """Convenient access to currently active objects.

        Note: Does not support assignment to window, buffer or tabpage.
        """

    @property
    def vars(self) -> "Variables":
        # pyre-ignore[7]:
        """An object providing access to global Vim variables."""

    @property
    def vvars(self) -> "Variables":
        # pyre-ignore[7]:
        """An object providing access to Vim (v:) variables."""

    @property
    def options(self) -> "GlobalOptions":
        # pyre-ignore[7]:
        """An object providing access to Vim's global options."""

    def eval(self, expr: str) -> Union[dict, list, str]:
        # pyre-ignore[7]:
        """Evaluate a Vim expression.

        :return:
            A dict, list or string. See :vim:`python-eval` for details.
        :raise VimError:
            A more detailed version vim.error (:vim:`python-error`).
        """

    def command(self, cmd: str) -> None:
        """Execute an Ex command.

        :cmd: The Ex command to execute:

        :raise VimError:
            A more detailed version vim.error (:vim:`python-error`).
        """


class _BufferDesc:
    """Wrapper around a :vim:`python-buffer`.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    A number of extensions to the standard :vim:`python-buffer` are provided.

    - The `vars` property provides access to the buffer's variables.
    - The `list` context manager provides a clean, and often more efficient,
      way to access the buffer's content.
    - The `temp_options` context manager provides a clean way to work with a
      buffer with some of its options temporarily modified.
    - Buffer specific meta-data can be attached using the `store`.
    - The values provided by :vim:`getbufinfo()` are effectively available as
      properties of this class.
    """
    __doc_shadow__ = 'Buffer'

    @property
    def bufnr(self) -> int:
        # pyre-ignore[7]:
        """The same as the `number` attribute.

        This exists as a side effect of providing :vim:`getbufinfo()` values as
        properties. It is more  efficient to use the `number` attribute.
        """

    @property
    def changed(self) -> int:
        # pyre-ignore[7]:
        """Modified flag; 0=unchanged, 1=changed."""

    @property
    def changedtick(self) -> int:
        # pyre-ignore[7]:
        """Same as :vim:`changetick`."""

    @property
    def hidden(self) -> int:
        # pyre-ignore[7]:
        """Hidden flag; 0=buffer visible in a window, 1=buffer hidden."""

    @property
    def lastused(self) -> int:
        # pyre-ignore[7]:
        """Time (in seconds) when buffer was last used.

        This is a time in seconds as returned by :vim:`localtime()`.
        """

    @property
    def lnum(self) -> int:
        # pyre-ignore[7]:
        """The current line number for the buffer."""

    @property
    def linecount(self) -> int:
        # pyre-ignore[7]:
        """The number of lines in the buffer."""

    @property
    def loaded(self) -> int:
        # pyre-ignore[7]:
        """Buffer loaded flag; 0=not loaded, 1=buffer loaded."""

    # TODO: Gives me attribute error. May be only available when at least one
    # sign is placed.
    # @property
    # def signs(self) -> int:
    #     # pyre-ignore[7]:
    #     """A list of all the signs placed in the buffer.
    #
    #     See :vim:`getbufinfo()` for more details.
    #     """

    @property
    def variables(self) -> 'Variables':
        # pyre-ignore[7]:
        """The same as the `vars` attribute.

        This exists as a side effect of providing :vim:`getbufinfo()` values as
        properties. It is more  efficient to use the `vars` attribute.
        """

    @property
    def windows(self) -> List[int]:
        # pyre-ignore[7]:
        """A list of window IDs for windows that are displaying this buffer.

        Each entry is a :vim:`window-ID`.
        """

    @property
    def popups(self) -> List[int]:
        # pyre-ignore[7]:
        """A list of window IDs for popups that are displaying this buffer.

        Each entry is a :vim:`window-ID`.
        """
