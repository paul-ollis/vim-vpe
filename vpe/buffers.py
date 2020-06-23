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
        self.__dict__['_cleared'] = False

    def range(self, a, b):
        return self._wrap_item(self._proxied.range(a, b))

    def __iter__(self):
        if self._is_cleared():
            return iter(())
        return iter(self._proxied)

    def __len__(self):
        return 0 if self._is_cleared() else len(self._proxied)

    def __getitem__(self, slice_or_index):
        if not isinstance(slice_or_index, slice):
            if self._is_cleared():
                raise IndexError(f'Index ({slice_or_index!r}) out of range')
            try:
                return super().__getitem__(slice_or_index)
            except IndexError:
                raise IndexError(f'Index ({slice_or_index!r}) out of range')

        if self._is_cleared():
            return []
        if slice.step is None:
            return super().__getitem__(slice_or_index)
        return list(self._proxied).__getitem__(slice_or_index)

    def __setitem__(self, slice_or_index, value):
        self._proxied.__setitem__(slice_or_index, value)

    @property
    def vars(self):
        """The buffar vars wrapped as a Variables instance."""
        # TODO: A circular import issue to be fixed.
        from vpe import variables
        return variables.Variables(self._proxied)

    def append(self, line_or_lines, nr=None):
        if self._is_cleared():
            if isinstance(line_or_lines, (list, tuple)):
                self._proxied[:] = line_or_lines
            else:
                self._proxied[0] = line_or_lines
        else:
            if nr is None:
                self._proxied.append(line_or_lines)
            else:
                self._proxied.append(line_or_lines, nr)
        self.__dict__['_cleared'] = False

    def _is_cleared(self):
        if self._cleared:
            if len(self._proxied) == 1 and self._proxied[0] == '':
                return True

    def clear(self):
        """Empty the buffer and behave as if it has no lines."""
        self._proxied[:] = []
        self.__dict__['_cleared'] = True


class Buffers(proxies.CollectionProxy):
    """Wrapper around the built-in vim.buffers.

    This is a proxy that extends the vim.Buffer behaviour in various ways.
    """
    @property
    def _proxied(self):
        return _vim.buffers


buffers = Buffers()
