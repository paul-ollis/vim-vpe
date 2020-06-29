"""Support for proxying of Vim objects."""

import abc
import collections.abc

import vim as _vim

import vpe

__all__ = ('Proxy', 'CollectionProxy', 'MutableMappingProxy')


def _resolve_proxied(obj):
    try:
        return _resolve_proxied(obj._proxied)
    except AttributeError:
        return obj


class Proxy:
    """Base for proxy classes.

    Subclasses must support the following protocol:

        - The proxied object is avalable as an attribute or property called
          '_proxied'.

        - May provide a _resolve_item method. Typically this will undo any
          proxy wrapping.

        - May provide a _wrap_item method. Typically this is used to wrap the
          value in a proxy.

    IMPORTANT
        This base class overrides __setattr__. Base classes should use
        self.__dict__ to explicitly set attribuyes (*e.g.* the _proxied
        attribute).
    """
    _writeable = set()

    def __init__(self, obj=None):
        if obj is not None:
            self.__dict__['_proxied'] = _resolve_proxied(obj)

    def __getattr__(self, name):
        return self._wrap_item(getattr(self._proxied, name), name)

    def __setattr__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value
        elif name in self._writeable:
            setattr(self._proxied, name, value)
        else:
            raise AttributeError(
                f'can\'t set attribute {name} for {self.__class__.__name__}')

    def _resolve_item(self, item):
        """Resolve an item.

        This default implementation will return the _proxied value, if present.
        """
        try:
            return item._proxied
        except AttributeError:
            return item

    def _wrap_item(self, item, name=None):
        """Optionally wrap an item.

        This default implementation uses a common wrapping function.
        """
        return vpe.wrap_item(item)


class CollectionProxy(Proxy, collections.abc.Collection):
    """Base for collection style proxy classes.

    This extends the behaviour so that retrieved values can get wrapped into
    more one of the *vpe* extended types.
    """
    def __contains__(self, item):
        return self._resolve_item(item) in self._proxied

    def __getitem__(self, key):
        return self._wrap_item(self._proxied[key])

    def __iter__(self):
        for item in self._proxied:
            yield self._wrap_item(item)

    def __len__(self):
        return len(self._proxied)


class MutableMappingProxy(CollectionProxy, collections.abc.MutableMapping):
    """Base for collection style proxy classes.

    This extends the behaviour so that retrieved values can get wrapped into
    more one of the *vpe* extended types.
    """
    def __setitem__(self, name, value):
        self._proxied[name] = value

    def __delitem__(self, name):
        del self._proxied[name]

    def keys(self):
        return self._proxied.keys()

    # TODO: This does not wrap the returned values.
    def values(self):
        return self._proxied.values()

    # TODO: This does not wrap the returned values.
    def items(self):
        return self._proxied.items()

    def update(self, *args, **kwargs):
        return self._proxied.update(*args, **kwargs)

    def get(self, key, default=None):
        return self._wrap_item(self._proxied.get(key, default), key)

    def pop(self, key, default=None):
        return self._wrap_item(self._proxied.pop(key, default), key)

    def popitem(self):
        key, value = self._proxied.popitem()
        return self._wrap_item(value, key)

    def has_key(self, key):
        return self._proxied.has_key(key)


class TemporaryOptions:
    def __init__(self, options):
        self.__dict__.update({
            '_options': options,
            '_saved' : {}
        })

    def __enter__(self):
        self._saved.clear()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for name, value in self._saved.items():
            self._options[name] = value

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def __setitem__(self, name, value):
        if name not in self._saved:
            self._saved[name] = self._options[name]
        self._options.__setattr__(name, value)
