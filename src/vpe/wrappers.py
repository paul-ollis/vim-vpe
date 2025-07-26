"""Wrappers around the built-in Vim Python types.

You should not normally need to import this module directly.
"""
# pylint: disable=too-many-lines
from __future__ import annotations

import collections
import itertools
import pathlib
import pprint
import weakref
from typing import (
    Any, Callable, ClassVar, Iterator, NamedTuple, Optional, Type)

import vim as _vim

from vpe import common
from vpe.vpe_lib import diffs, resources

__all__ = ('tabpages', 'TabPage', 'Vim', 'Registers', 'vim',
           'Function', 'windows', 'Window',
           'buffers', 'Buffer', 'Range', 'Struct', 'VI_DEFAULT')
__api__ = ('Function', 'Commands')

# Type aliases
ListenerCallbackFunc = Callable[[int, int, int, int, list[dict]], None]
ListenerCallbackMethod = Callable[[int, int, int, list[dict]], None]

# Special values used to reset represent Vi or Vim default values. Currently
# only used to set options.
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
        if name not in self.__dict__ and name.startswith('_'):
            # Non-simple names should not default to ``None``.
            cname = self.__class__.__name__
            raise AttributeError(
                f'{cname!r} object has no attribute {name!r}')
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
            # pylint: disable=unnecessary-dunder-call
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


class BufListener(common.Callback):
    """A Pythonic wrapping of Vim's listener... functions.

    One of these is created by `Buffer.add_listener`. Direct instantiation of
    this class is not recommended or supported.

    :func:        The Python function or method to be called back.
    :buf:         The `Buffer` instance.
    :is_method:   If set then the buffer is not provided to callbacks.
    :raw_changes: Include the raw changes as an additional argument:

    @listen_id: The unique ID from a :vim:`listener_add` invocation.
    """
    listen_id: int

    def __init__(
            self, func, buf, is_method: bool, ops: bool = True,
            raw_changes: bool = False,
        ):
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        super().__init__(func)
        self.buf = buf
        self.is_method = is_method
        self.ops = ops
        self.raw_changes = raw_changes

    def flush(self):
        """Request that any pending callbacks are invoked for this listener."""
        vim.listener_flush(self.buf.number)

    def invoke_self(self, vpe_args):
        """Invoke this Callback.

        This extends the `Callback.invoke_self` method.

        The vpe_args['args'] are (From Vim's docs):

        bufnr
            The buffer that was changed
        start
            First changed line number
        end
            First line number below the change
        added
            Number of lines added, negative if lines were deleted
        changes
            A List of items with details about the changes

        The ``bufnr`` is ignored, since this is just self.buf.number.

        Start and end are adjusted so they form a Python range.

        If `ops` is True then a list of operations is provided to the callback.
        Each entry in the changes is converted to one of a `BufAddOp`,
        `BufDeleteOp` or `BufChangeOp`.
        """
        _, start, end, added, changes = vpe_args['args']
        start -= 1
        end -= 1
        if self.is_method:
            vpe_args['args'] = start, end, added
        else:
            vpe_args['args'] = self.buf, start, end, added
        if self.ops:
            vpe_changes = [diffs.BufOperation.create(**ch) for ch in changes]
            vpe_args['args'] += (vpe_changes,)
        if self.raw_changes:
            vpe_args['args'] += (changes,)
        super().invoke_self(vpe_args)

    def stop_listening(self):
        """Stop listening for changes.

        This permanently disables this listener.
        """
        vim.listener_remove(self.listen_id)


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
    # pylint: disable=too-many-public-methods
    _known: dict[int, "Buffer"] = {}
    _writeable = set(('name',))

    def __init__(self, buffer):
        self.__dict__['_number'] = buffer.number
        self.__dict__['_store'] = collections.defaultdict(Struct)
        self._known[buffer.number] = self
        self.__dict__['_marker_sets']: dict[str, MarkerSet] = {}
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

    def retrieve_store(self, key: Any) -> Struct | None:
        """Retrive a given buffer store if it exists.

        This is similar to `store`, but no new store is created.

        :return:
            The requested store `Struct` or ``None`` if it does not exist.
        """
        if key in self._store:
            return self._store[key]
        else:
            return None

    # TODO: I think the docstring is wrong; 'a' is a line number, not an index.
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
        try:
            if nr is None:
                self._proxied.append(line_or_lines)
            else:
                self._proxied.append(line_or_lines, nr)
        except vim.error:
            # I have seen this happen when appending to the log buffer. Trying
            # to log an error is therefore a *bad* idea.
            #
            # TODO: Could we check this is not the log buffer?
            pass

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

    def find_active_windows(self, all_tabpages=False) -> list['Window']:
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

        found: dict[int, 'Window'] = {}
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
            func: ListenerCallbackFunc | ListenerCallbackMethod,
            ops: bool = True,
            raw_changes: bool = False,
        ) -> BufListener:
        """Add a callback for changes to this buffer.

        This is implemented using :vim:`listener_add()`

        :func:
            The callback function which is invoked with the following
            arguments:

            :buf:
                The buffer that was changed. Only present if *func* is not a
                bound method of this instance.
            :start:
                Start of the range of modified lines (zero based).
            :end:
                End of the range of modified lines.
            :added:
                Number of lines added, negative if lines were deleted.

        :ops:
            Include a list of the individal operations to the callback. This is
            ``True`` by default.

            :changed:
                A list of diffs.BufOperation instances with details about the
                changes.

        :raw_changes:
            Include the raw changes as an additional argument:

            :raw_changes:
                The unmodified changes provided by the Vim buffer change
                callback (see :vim:`listener_add` for details).

        :return:
            A :py:obj:`BufListener` object.
        """
        inst = getattr(func, '__self__', None)
        p_buf = weakref.proxy(self)
        if inst is self:
            cb = BufListener(
                func, p_buf, is_method=True, raw_changes=raw_changes)
        else:
            cb = BufListener(
                func, p_buf, is_method=False, raw_changes=raw_changes)
        cb.listen_id = vim.listener_add(cb.as_vim_function(), self.number)
        return cb

    def clear_props(self):
        """Remove all properties from all line in this buffer."""
        vim.prop_clear(1, len(self), {'bufnr': self.number})

    def set_line_prop(
            self, lidx: int, start_cidx: int, end_cidx: int, hl_group: str,
            name: str = ''):
        """Set a highlighting property on a single line.

        :lidx:        The index of the line to hold the property.
        :start_cidx:  The index within the line where the property starts.
        :end_cidx:    The index within the line where the property ends.
        :hl_group:    The name of the highlight group to use.
        :name:        An optional name for the property.
        """
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=too-many-arguments
        prop_type_name = f'vpe:hl:{name or hl_group}'
        args = {'bufnr': self.number}
        props = vim.prop_type_get(prop_type_name, args)
        if not props:
            args['highlight'] = hl_group
            vim.prop_type_add(prop_type_name, args)
        args = {
            'type': prop_type_name,
            'bufnr': self.number,
            'end_col': end_cidx + 1,
        }
        vim.prop_add(lidx + 1, start_cidx + 1, args)

    def set_property_type(
            self,
            name: str,
            **kwargs):
        """Register or modify a property type associated with this buffer.

        This is a wrapper around vim.prop_type_add and vim.prop_type_change.

        :kwargs:
            The same parameters used for vim.prop_type_add's props argument;
            namely::

                highlight: str
                priority: int
                combine: bool
                override: bool
                start_incl: bool
                end_incl: bool
        """
        args = kwargs.copy()
        if not vim.prop_type_get(name):
            args['bufnr'] = self.number
            vim.prop_type_add(name, args)
        else:
            vim.prop_type_change(name, args)

    def marker_set(self, name: str):
        """Get the marker set with a given name.

        The marker set for a given name is created on demand.
        """
        if name not in self._marker_sets:
            self._marker_sets[name] = MarkerSet(self, name)
        return self._marker_sets[name]

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
    def visible_line_range(self) -> tuple[int, int]:
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

    @staticmethod
    def win_id_to_window(win_id: str) -> Window | None:
        """Return the window corresponding to a given window ID."""
        win_index = vim.win_id2win(win_id) - 1
        if win_index >= 0:
            try:
                return windows[win_index]
            except IndexError:
                return None
        else:
            return None


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
    _writeable: set[str] = set()

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
            if name.startswith('__'):
                # Special names should not default to ``None``.
                cname = self.__class__.__name__
                raise AttributeError(
                    f'{cname!r} object has no attribute {name!r}')
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
    def _split(_s: str) -> list[str]:
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
    def __getitem__(self, reg_name: str | int) -> Any:
        """Allow reading registers as dictionary entries.

        The reg_name may also be an integer value in the range 0-9.
        """
        return common.vim_simple_eval(f'@{reg_name}')

    def __setitem__(self, reg_name: str | int, value: Any):
        """Allow setting registers as dictionary entries.

        The reg_name may also be an integer value in the range 0-9.
        """
        vim.setreg(f'{reg_name}', value)


class Command:
    """Wrapper to invoke a Vim command as a function.

    The `Commands` class creates instances of this; direct instantiation by
    users is not intended.

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
    :silent:     Run with the silent command modifier.
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
    mod_names = (
        'silent',
        'vertical', 'aboveleft', 'belowright', 'topleft', 'botright',
        'keepalt')

    def __init__(self, name, modifiers: dict[str, bool]):
        self.name = name
        self.modifiers = modifiers.copy()

    def __call__(
            self, *args, bang=False, lrange='', a='', b='', preview=False,
            keepalt=True, file=None, **modifiers):
        # pylint: disable=too-many-arguments,too-many-branches,too-many-locals
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
        mod_args.update(self.modifiers)
        mod_args.update(modifiers)
        cmd_mods = " ".join(mod for mod in self.mod_names if mod_args.get(mod))
        if cmd_mods:
            cmd = f'{cmd_mods} {range_expr}{cmd}{arg_expr}'
        else:
            cmd = f'{range_expr}{cmd}{arg_expr}'
        if not preview:
            common.vim_command(cmd)
        if file:
            file.write(f'{cmd}\n')
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

    Each command function is actually an instance of the :py:obj:`Command`
    class. See its description for details of the arguments.

    Most commands that can be entered at the colon prompt are supported.
    Structural parts of vim-script (such as function, while, try, *etc*) are
    excluded.

    The vpe, vpe.mapping and vpe.syntax modules provides some functions and
    classes as alternatives for some commands. You are encouraged to use these
    alternatives in preference to the equivalent functions provided here. The
    following is a summary of the alternatives.

    `vpe.AutoCmdGroup`
        A replacement for augroup and autocmd.

    `vpe.highlight`
        Provides keyword style arguments. See also the `syntax` module.

    `vpe.error_msg`
        Writes a message with error highlightling, but does not raise a
        vim.error.

    `mapping`
        This provides functions to make key mappings that are handled by Python
        functions.

    `syntax`
        Provides a set of classes, functions and context managers to help
        define syntax highlighting.

    See also: `vpe.pedit`.

    :modifiers:
        A dictionary of the default modifier flags for generated
        :py:obj:`Command` instances. This is only intended to be used by the
        `with_modifiers` class method.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, modifiers: dict[str, bool] = None):
        self.modifiers = modifiers.copy() if modifiers else {}

    def __getattr__(self, name: str) -> Command:
        if name.startswith('__'):
            raise AttributeError(
                f'No command function called {name!r} available')

        cname_form = f':{name}'
        if common.vim_simple_eval(f'exists({cname_form!r})') == '2':
            if name not in _blockedVimCommands:
                return Command(name, self.modifiers)

        raise AttributeError(
            f'No command function called {name!r} available')

    @classmethod
    def with_modifiers(cls, **modifiers):
        """Return a version of ``Commands`` that always applies modifiers.

        For example:<py>:

            silent = vpe.commands.modified(silent=True)
            silent.tabonly()

        Is equivalent to:<py>:

            vpe.commands.tabonly(silent=True)
        """
        return cls(modifiers)


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
    def iter_all_windows() -> Iterator[tuple[TabPage, Window]]:
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
        # TODO:
        #   Look at ways to use _vim.Function(name) for built-in functions.
        #   Lookup time and
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
        # This can be useful for debugging, but be careful which functions are
        # selected.
        # pylint: disable=condition-evals-to-constant
        if False and 'listen' in self.name:
            common.call_soon(print, f'Function.__call__: {self.name}'
                   f' vim.state()={_vim.eval("state()")}')
            for i, a in enumerate(args):
                common.call_soon(print, f' args[{i}] ={a}')
        # pylint: enable=condition-evals-to-constant
        if suppress_vim_invocation_errors.active:
            v = super().__call__(*args, **kwargs)  # pylint: disable=no-member
        else:
            try:
                # pylint: disable=no-member
                v = super().__call__(*args, **kwargs)
            except Exception as e:
                args_lines = pprint.pformat(args).splitlines()
                kwargs_lines = pprint.pformat(kwargs).splitlines()
                call_soon = common.call_soon
                call_soon(print, f'VPE: Function.__call__ failed: {type(e)}, {e}')
                call_soon(print, f'    self.name={self.name}')
                call_soon(print, f'    self.args={self.args}')
                call_soon(print, f'    self.self={self.self}')
                call_soon(print, f'    args={args_lines[0]}')
                for line in args_lines[1:]:
                    call_soon(print, f'         {line}')
                call_soon(print, f'    kwargs={kwargs_lines[0]}')
                for line in kwargs_lines[1:]:
                    call_soon(print, f'           {line}')
                call_soon(print, f'    vim.state()={_vim.eval("state()")}')
                if isinstance(e, vim.error):
                    raise common.VimError(e)
                raise                                            # pragma: no cover
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


class _ErrorSuppressor:
    """A context that suppresses logging details of failed Vim functions."""

    def __init__(self):
        self._count = 0

    @property
    def active(self) -> bool:
        """Flag indication that error supporession is active."""
        return self._count > 0

    def __enter__(self):
        self._count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._count -= 1
        return exc_val is not None and isinstance(exc_val, vim.error)


# Context manager used to prevent logging of Vim function call errors.
suppress_vim_invocation_errors = _ErrorSuppressor()


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

    def eval(self, expr: str) -> dict | list | str:
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
    def windows(self) -> list[int]:
        # pyre-ignore[7]:
        """A list of window IDs for windows that are displaying this buffer.

        Each entry is a :vim:`window-ID`.
        """

    @property
    def popups(self) -> list[int]:
        # pyre-ignore[7]:
        """A list of window IDs for popups that are displaying this buffer.

        Each entry is a :vim:`window-ID`.
        """
