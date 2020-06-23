"""Special support for vim variables."""

import vim as _vim

__all__ = ('Variables',)

from vpe import dictionaries
from vpe import options
from vpe import proxies


class ImmutableVariables(dictionaries.Dictionary):
    """Wrapper around the various vim variables dictionaries.

    This extends the behaviour so that the members appear as attributes. It is
    immutable in the sense that attributes cannot be added or removed. However,
    individual entries may be modified.
    """
    def __getattr__(self, name):
        if name not in self._proxied:
            raise AttributeError(
                f'{self.__class__.__name__} object has no attribute {name!r}')
        return self._wrap_item(self._proxied[name], name)


class Variables(ImmutableVariables):
    """Wrapper around the various vim variables dictionaries.

    This allows entries to be added and removed.
    """
    def __setattr__(self, name, value):
        self._proxied[name] = self._resolve_item(value)


vars = Variables(_vim.vars)
vvars = Variables(_vim.vvars)
