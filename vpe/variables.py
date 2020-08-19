"""Special support for vim variables."""

import vim as _vim

__all__ = ('Variables',)

import vpe
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
            return None
            raise AttributeError(
                f'{self.__class__.__name__} object has no attribute {name!r}')
        return self._wrap_item(self._proxied[name], name)


class Variables(ImmutableVariables):
    """Wrapper around the various vim variables dictionaries.

    This allows entries to be modified.
    """
    def __setattr__(self, name, value):
        self._proxied[name] = self._resolve_item(value)


class VimVariables(ImmutableVariables):
    """Wrapper around the various vim variables dictionaries.

    This is necessary to allow operations such as vim.vvars.errmsg = ''. The vim.vvars
    object has locked == FIXED. So we need to set variables using the good old
    'let' command.
    """
    def __setattr__(self, name, value):
        try:
            vpe.vim_command(f'let v:{name} = {value!r}')
        except _vim.error:
            vpe.vim_command(f'let v:errmsg = ""')
            raise AttributeError(
                f'can\'t set attribute {name} for {self.__class__.__name__}')


vars = Variables(_vim.vars)
vvars = VimVariables(_vim.vvars)
