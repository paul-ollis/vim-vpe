"""
A library of various helpers functions and classes
"""
import inspect
import sys
import socket
import logging
import threading
import time
import random


class MissingModule(object):
    __slots__ = ["__name"]

    def __init__(self, name):
        self.__name = name

    def __getattr__(self, name):
        if name.startswith("__"):  # issue 71
            raise AttributeError("module %r not found" % (self.__name,))
        raise ImportError("module %r not found" % (self.__name,))

    def __bool__(self):
        return False
    __nonzero__ = __bool__


class hybridmethod(object):
    """Decorator for hybrid instance/class methods that will act like a normal
    method if accessed via an instance, but act like classmethod if accessed
    via the class."""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        return self.func.__get__(cls if obj is None else obj, obj)

    def __set__(self, obj, val):
        raise AttributeError("Cannot overwrite method")


def get_id_pack(obj):
    """introspects the given "local" object, returns id_pack as expected by BaseNetref

    The given object is "local" in the sense that it is from the local cache. Any object in the local cache exists
    in the current address space or is a netref. A netref in the local cache could be from a chained-connection.
    To handle type related behavior properly, the attribute `__class__` is a descriptor for netrefs.

    So, check thy assumptions regarding the given object when creating `id_pack`.
    """
    if hasattr(obj, '____id_pack__'):
        # netrefs are handled first since __class__ is a descriptor
        return obj.____id_pack__
    elif inspect.ismodule(obj) or getattr(obj, '__name__', None) == 'module':
        # TODO: not sure about this, need to enumerate cases in units
        if isinstance(obj, type):  # module
            obj_cls = type(obj)
            name_pack = '{0}.{1}'.format(obj_cls.__module__, obj_cls.__name__)
            return (name_pack, id(type(obj)), id(obj))
        else:
            if inspect.ismodule(obj) and obj.__name__ != 'module':
                if obj.__name__ in sys.modules:
                    name_pack = obj.__name__
                else:
                    name_pack = '{0}.{1}'.format(obj.__class__.__module__, obj.__name__)
            elif inspect.ismodule(obj):
                name_pack = '{0}.{1}'.format(obj__module__, obj.__name__)
                print(name_pack)
            elif hasattr(obj, '__module__'):
                name_pack = '{0}.{1}'.format(obj.__module__, obj.__name__)
            else:
                obj_cls = type(obj)
                name_pack = '{0}'.format(obj.__name__)
            return (name_pack, id(type(obj)), id(obj))
    elif not inspect.isclass(obj):
        name_pack = '{0}.{1}'.format(obj.__class__.__module__, obj.__class__.__name__)
        return (name_pack, id(type(obj)), id(obj))
    else:
        name_pack = '{0}.{1}'.format(obj.__module__, obj.__name__)
        return (name_pack, id(obj), 0)


def get_methods(obj_attrs, obj):
    """introspects the given (local) object, returning a list of all of its
    methods (going up the MRO).

    :param obj: any local (not proxy) python object

    :returns: a list of ``(method name, docstring)`` tuples of all the methods
              of the given object
    """
    methods = {}
    attrs = {}
    if isinstance(obj, type):
        # don't forget the darn metaclass
        mros = list(reversed(type(obj).__mro__)) + list(reversed(obj.__mro__))
    else:
        mros = reversed(type(obj).__mro__)
    for basecls in mros:
        attrs.update(basecls.__dict__)
    for name, attr in attrs.items():
        if name not in obj_attrs and hasattr(attr, "__call__"):
            methods[name] = inspect.getdoc(attr)
    return methods.items()
