"""Enhanced buffer support.

This module provides the `Buffer` and `Range` classes. Normally you work with
these classes via the `Vim` class:<py>:

    lines = list(vim.current.buffer)
    buf = vim.buffers[3]

You should not normally need to import this module directly.
"""

from __future__ import annotations

import collections
import weakref

import vim as _vim

import vpe
from vpe import proxies

__all__ = ('buffers', 'Buffer', 'Range', 'Struct')


class Struct:
    """A basic data storage structure.

    This is intended to store arbitrary name, value pairs as attributes.
    Attempting to read an undefined attribute gives ``None``.

    This is provided primarily to support the `Buffer.store` mechanism. Direct
    use of this class is not intended as part of the API.
    """
    def __getattr__(self, name):
        setattr(self, name, None)


class BufferListContext(list):
    """Context manager providing a temporary list of a buffer's lines."""
    def __init__(self, vim_buffer):
        super().__init__(vim_buffer)
        self._vim_buffer = weakref.ref(vim_buffer)
        self.abort = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.abort:
            return
        b = self._vim_buffer()
        if exc_type is None and b is not None :
            with b.temp_options(modifiable=True):
                b[:] = self


# TODO: CollectionProxy is not the correct base class.
class Range(proxies.CollectionProxy):
    """Wrapper around the built-in vim.Range type.

    This is a proxy that extends the vim.Buffer behaviour in various ways.
    """
    def append(self, line_or_lines, nr=None):
        if nr is None:
            self._proxied.append(line_or_lines)
        else:
            self._proxied.append(line_or_lines, nr)

    def __setitem__(self, slice_or_index, value):
        self._proxied.__setitem__(slice_or_index, value)


# TODO: CollectionProxy is not the correct base class.
class Buffer(proxies.CollectionProxy):
    """Wrapper around a :vim:`python-window`.

    VPE creates and manages instances of this class as required. It is not
    intended that user code creates Buffer instances directly.

    A number of extensions to the standard :vim:`python-buffer` are provided.

    - The `vars` property provides access to the buffer's variables.
    - The `list` context manager provides a clean, and often more efficient,
      way to access the buffer's content.
    - The `temp_options` context manager provides a clean way to work with a
      buffer with some of its options temporarily modified.
    - Buffer specific meta-data can be attached using the `store`.
    """
    _known = {}
    _writeable = set(('name',))

    def __init__(self, buffer):
        super().__init__()
        self.__dict__['number'] = buffer.number
        self.__dict__['_store'] = collections.defaultdict(Struct)
        self._known[buffer.number] = self

    def store(self, key: Any) -> Struct:
        """Return a `Struct` for a give key.

        This provides a mechanism to store arbitrary data associated with a
        given buffer. A new `Struct` is created the first time a given key is
        used. An example of how this can be used:<py>:

            vim.current.buffer.store['my-store'].processed = True
            ...
            for buf in vim.buffers:
                if buf.store['my-store].processed:
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
        return self._wrap_item(self._proxied.range(a, b))

    def __iter__(self):
        return iter(self._proxied)

    def __setitem__(self, slice_or_index, value):
        self._proxied.__setitem__(slice_or_index, value)

    def __delitem__(self, slice_or_index):
        self._proxied.__delitem__(slice_or_index)

    @classmethod
    def get_known(cls, buffer):
        return cls._known.get(buffer.number, None)

    @property
    def vars(self) -> vpe.variables.Variables:
        """The buffar vars wrapped as a `Variables` instance."""
        return vpe.variables.Variables(self._proxied.vars)

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

            with vim.current.buffer.lines() as lines:
                # Now lines is a copy of the buffers lines.
                lines[2:4] = ['one']  # Update lines in-place.

            # The vim.current.buffer has now been updated with modified lines.

        Although this involves taking a copy of the buffer's lines and then
        completely replacing the buffer's set of lines, this is a much more
        efficient way to make non-trivial modifications to a buffer's contents.

        This will update the buffer, even if 'modifiable' is not set.
        """
        return BufferListContext(self)

    def temp_options(self, **presets):
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
        return proxies.TemporaryOptions(self.options, **presets)

    @property
    def _proxied(self):
        return _vim.buffers[self.number]


class Buffers(proxies.CollectionProxy):
    """Wrapper around the built-in vim.buffers.

    This is a proxy that extends the vim.Buffer behaviour in various ways.
    """
    @property
    def _proxied(self):
        return _vim.buffers


buffers = Buffers()
