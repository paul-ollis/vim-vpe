"""Special support for buffers."""

import vim as _vim

from vpe import proxies

__all__ = ('buffers',)


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

    def __getitem__(self, slice_or_index):
        if not isinstance(slice_or_index, slice):
            try:
                return super().__getitem__(slice_or_index)
            except IndexError:
                raise IndexError(f'Index ({slice_or_index!r}) out of range')

        if slice.step is None:
            return super().__getitem__(slice_or_index)
        return list(self._proxied).__getitem__(slice_or_index)

    def __setitem__(self, slice_or_index, value):
        self._proxied.__setitem__(slice_or_index, value)


class Buffer(proxies.CollectionProxy):
    """Wrapper around the built-in vim.Buffer type.

    This is a proxy that extends the vim.Buffer behaviour in various ways.
    """
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
        return variables.Variables(self._proxied)

    def append(self, line_or_lines, nr=None):
        if nr is None:
            self._proxied.append(line_or_lines)
        else:
            self._proxied.append(line_or_lines, nr)

    def view(self):
        """A sequence context for efficient buffer modification."""
        return BufferView(self)

    def temp_options(self):
        """Context used to temporarily change options."""
        return proxies.TemporaryOptions(self.options)


class Buffers(proxies.CollectionProxy):
    """Wrapper around the built-in vim.buffers.

    This is a proxy that extends the vim.Buffer behaviour in various ways.
    """
    @property
    def _proxied(self):
        return _vim.buffers


buffers = Buffers()
