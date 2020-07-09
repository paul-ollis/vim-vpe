"""Special support for buffers."""

import weakref

import vim as _vim

from vpe import proxies

__all__ = ('buffers',)


class BufferListContext(list):
    def __init__(self, vim_buffer):
        super().__init__(vim_buffer)
        self._vim_buffer = weakref.ref(vim_buffer)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        b = self._vim_buffer()
        if exc_type is None:
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


class Buffer(proxies.CollectionProxy):
    """Wrapper around the built-in vim.Buffer type.

    This is a proxy that extends the vim.Buffer behaviour in various ways.
    """
    _writeable = set(('name',))

    def __init__(self, buffer):
        super().__init__(buffer)

    def range(self, a, b):
        return self._wrap_item(self._proxied.range(a, b))

    def __iter__(self):
        return iter(self._proxied)

    def __setitem__(self, slice_or_index, value):
        self._proxied.__setitem__(slice_or_index, value)

    @property
    def vars(self):
        """The buffar vars wrapped as a Variables instance."""
        # TODO: A circular import issue to be fixed.
        from vpe import variables
        return variables.Variables(self._proxied.vars)

    def append(self, line_or_lines, nr=None):
        if nr is None:
            self._proxied.append(line_or_lines)
        else:
            self._proxied.append(line_or_lines, nr)

    def list(self):
        """A sequence context for efficient buffer modification."""
        return BufferListContext(self)

    def temp_options(self, **presets):
        """Context used to temporarily change options."""
        return proxies.TemporaryOptions(self.options, **presets)


class Buffers(proxies.CollectionProxy):
    """Wrapper around the built-in vim.buffers.

    This is a proxy that extends the vim.Buffer behaviour in various ways.
    """
    @property
    def _proxied(self):
        return _vim.buffers


buffers = Buffers()
