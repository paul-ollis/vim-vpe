"""The RPyC protocol."""
import itertools
import pickle
import sys

from . import brine, consts, netref, vinegar
from ..lib import get_id_pack, get_methods
from ..lib.colls import RefCountingColl, WeakValueDict

#: The default configuration dictionary of the protocol. You can override these parameters
#: by passing a different configuration dict to the :class:`Connection` class.
#:
#: .. note::
#:    You only need to override the parameters you want to change. There's no need
#:    to repeat parameters whose values remain unchanged.
#:
#: ======================================= =============== =====================================================
#: Parameter                               Default value   Description
#: ======================================= =============== =====================================================
#: ``allow_safe_attrs``                    ``True``        Whether to allow the use of *safe* attributes
#:                                                         (only those listed as ``safe_attrs``)
#: ``allow_exposed_attrs``                 ``True``        Whether to allow exposed attributes
#:                                                         (attributes that start with the ``exposed_prefix``)
#: ``allow_public_attrs``                  ``False``       Whether to allow public attributes
#:                                                         (attributes that don't start with ``_``)
#: ``allow_all_attrs``                     ``False``       Whether to allow all attributes (including private)
#: ``safe_attrs``                          ``set([...])``  The set of attributes considered safe
#: ``exposed_prefix``                      ``"exposed_"``  The prefix of exposed attributes
#: ``allow_getattr``                       ``True``        Whether to allow getting of attributes (``getattr``)
#: ``allow_setattr``                       ``False``       Whether to allow setting of attributes (``setattr``)
#: ``allow_delattr``                       ``False``       Whether to allow deletion of attributes (``delattr``)
#: ``allow_pickle``                        ``False``       Whether to allow the use of ``pickle``
#:
#: ``include_local_traceback``             ``True``        Whether to include the local traceback
#:                                                         in the remote exception
#: ``instantiate_custom_exceptions``       ``False``       Whether to allow instantiation of
#:                                                         custom exceptions (not the built in ones)
#: ``import_custom_exceptions``            ``False``       Whether to allow importing of
#:                                                         exceptions from not-yet-imported modules
#: ``instantiate_oldstyle_exceptions``     ``False``       Whether to allow instantiation of exceptions
#:                                                         which don't derive from ``Exception``. This
#:                                                         is not applicable for Python 3 and later.
#: ``propagate_SystemExit_locally``        ``False``       Whether to propagate ``SystemExit``
#:                                                         locally (kill the server) or to the other
#:                                                         party (kill the client)
#: ``propagate_KeyboardInterrupt_locally`` ``False``       Whether to propagate ``KeyboardInterrupt``
#:                                                         locally (kill the server) or to the other
#:                                                         party (kill the client)
#: ``logger``                              ``None``        The logger instance to use to log exceptions
#:                                                         (before they are sent to the other party)
#:                                                         and other events. If ``None``, no logging takes place.
#:
#: ``connid``                              ``None``        **Runtime**: the RPyC connection ID (used
#:                                                         mainly for debugging purposes)
#: ``credentials``                         ``None``        **Runtime**: the credentails object that was returned
#:                                                         by the server's :ref:`authenticator <api-authenticators>`
#:                                                         or ``None``
#: ``endpoints``                           ``None``        **Runtime**: The connection's endpoints. This is a tuple
#:                                                         made of the local socket endpoint (``getsockname``) and the
#:                                                         remote one (``getpeername``). This is set by the server
#:                                                         upon accepting a connection; client side connections
#:                                                         do no have this configuration option set.
#:
#: ``sync_request_timeout``                ``30``          Default timeout for waiting results
#: ======================================= =============== =====================================================
DEFAULT_CONFIG = dict(
    # ATTRIBUTES
    allow_safe_attrs=True,
    allow_exposed_attrs=True,
    allow_public_attrs=False,
    allow_all_attrs=False,
    safe_attrs=set([
        '__abs__', '__add__', '__and__', '__bool__', '__cmp__', '__contains__',
        '__delitem__', '__delslice__', '__div__', '__divmod__', '__doc__',
        '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
        '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__',
        '__iand__', '__idiv__', '__ifloordiv__', '__ilshift__', '__imod__',
        '__imul__', '__index__', '__int__', '__invert__', '__ior__',
        '__ipow__', '__irshift__', '__isub__', '__iter__', '__itruediv__',
        '__ixor__', '__le__', '__len__', '__long__', '__lshift__', '__lt__',
        '__mod__', '__mul__', '__ne__', '__neg__', '__new__', '__nonzero__',
        '__oct__', '__or__', '__pos__', '__pow__', '__radd__', '__rand__',
        '__rdiv__', '__rdivmod__', '__repr__', '__rfloordiv__', '__rlshift__',
        '__rmod__', '__rmul__', '__ror__', '__rpow__', '__rrshift__',
        '__rshift__', '__rsub__', '__rtruediv__', '__rxor__', '__setitem__',
        '__setslice__', '__str__', '__sub__', '__truediv__', '__xor__', 'next',
        '__length_hint__', '__enter__', '__exit__', '__next__', '__format__',
    ]),
    exposed_prefix="exposed_",
    allow_getattr=True,
    allow_setattr=False,
    allow_delattr=False,
    # EXCEPTIONS
    include_local_traceback=True,
    instantiate_custom_exceptions=False,
    import_custom_exceptions=False,
    instantiate_oldstyle_exceptions=False,  # which don't derive from Exception
    propagate_SystemExit_locally=False,  # whether to propagate SystemExit locally or to the other party
    propagate_KeyboardInterrupt_locally=True,  # whether to propagate KeyboardInterrupt locally or to the other party
    log_exceptions=True,
    # MISC
    allow_pickle=False,
    connid=None,
    credentials=None,
    endpoints=None,
    logger=None,
    sync_request_timeout=30,
    before_closed=None,
    close_catchall=False,
)

_connection_id_generator = itertools.count(1)


class Connection(object):
    """The RPyC *connection* (AKA *protocol*).

    :param root: the :class:`~rpyc.core.service.Service` object to expose
    :param channel: the :class:`~rpyc.core.channel.Channel` over which messages are passed
    :param config: the connection's configuration dict (overriding parameters
                   from the :data:`default configuration <DEFAULT_CONFIG>`)
    """

    def __init__(self, root, channel, config={}):
        self._closed = True
        self._config = DEFAULT_CONFIG.copy()
        self._config.update(config)
        if self._config["connid"] is None:
            self._config["connid"] = "conn%d" % (next(_connection_id_generator),)

        self._HANDLERS = self._request_handlers()
        self._channel = channel
        self._seqcounter = itertools.count()
        self._request_callbacks = {}
        self._local_objects = RefCountingColl()
        self._last_traceback = None
        self._proxy_cache = WeakValueDict()
        self._netref_classes_cache = {}
        self._remote_root = None
        self._send_queue = []
        self._local_root = root
        self._closed = False

    def __del__(self):
        self.close()

    def __repr__(self):
        a, b = object.__repr__(self).split(" object ")
        return "%s %r object %s" % (a, self._config["connid"], b)

    def _cleanup(self, _anyway=True):  # IO
        if self._closed and not _anyway:
            return
        self._closed = True
        self._channel.close()
        self._local_root.on_disconnect(self)
        self._request_callbacks.clear()
        self._local_objects.clear()
        self._proxy_cache.clear()
        self._netref_classes_cache.clear()
        self._last_traceback = None
        self._remote_root = None
        self._local_root = None
        del self._HANDLERS

    def close(self):  # IO
        """closes the connection, releasing all held resources"""
        if self._closed:
            return
        try:
            self._closed = True
            if self._config.get("before_closed"):
                self._config["before_closed"](self.root)
            self._async_request(consts.HANDLE_CLOSE)
        except EOFError:
            pass
        except Exception:
            if not self._config["close_catchall"]:
                raise
        finally:
            self._cleanup(_anyway=True)

    @property
    def closed(self):  # IO
        """Indicates whether the connection has been closed or not"""
        return self._closed

    def _box(self, obj):  # boxing
        """store a local object in such a way that it could be recreated on
        the remote party either by-value or by-reference"""
        if brine.dumpable(obj):
            return consts.LABEL_VALUE, obj
        if type(obj) is tuple:
            return consts.LABEL_TUPLE, tuple(self._box(item) for item in obj)
        elif isinstance(obj, netref.BaseNetref) and obj.____conn__ is self:
            return consts.LABEL_LOCAL_REF, obj.____id_pack__
        else:
            id_pack = get_id_pack(obj)
            self._local_objects.add(id_pack, obj)
            # print(f'Local add: {id_pack}, {obj}')
            return consts.LABEL_REMOTE_REF, id_pack

    def _unbox(self, package):  # boxing
        """Recreate a local object representation of the remote object.

        If the object is passed by value, just return it; if the object is
        passed by reference, create a netref to it.
        """
        label, value = package
        if label == consts.LABEL_VALUE:
            return value
        if label == consts.LABEL_TUPLE:
            return tuple(self._unbox(item) for item in value)
        if label == consts.LABEL_LOCAL_REF:
            return self._local_objects[value]
        if label == consts.LABEL_REMOTE_REF:
            id_pack = (str(value[0]), value[1], value[2])  # so value is a id_pack
            if id_pack in self._proxy_cache:
                proxy = self._proxy_cache[id_pack]
                proxy.____refcount__ += 1  # if cached then remote incremented refcount, so sync refcount
            else:
                try:
                    proxy = self._netref_factory(id_pack)
                except:
                    from pprint import pformat
                    print(pformat(id_pack))
                    raise
                self._proxy_cache[id_pack] = proxy
                # print(f'Proxy add: {id_pack}, {type(proxy)}')
            return proxy
        raise ValueError("invalid label %r" % (label,))

    def _netref_factory(self, id_pack):  # boxing
        """id_pack is for remote, so when class id fails to directly match """
        cls = None
        if id_pack[2] == 0 and id_pack in self._netref_classes_cache:
            cls = self._netref_classes_cache[id_pack]
        elif id_pack[0] in netref.builtin_classes_cache:
            cls = netref.builtin_classes_cache[id_pack[0]]
        if cls is None:
            # in the future, it could see if a sys.module cache/lookup hits first
            cls_methods = self.sync_request(consts.HANDLE_INSPECT, id_pack)
            cls = netref.class_factory(id_pack, cls_methods)
            if id_pack[2] == 0:
                # only use cached netrefs for classes
                # ... instance caching after gc of a proxy will take some mental gymnastics
                self._netref_classes_cache[id_pack] = cls
        return cls(self, id_pack)

    def _box_exc(self, typ, val, tb):  # dispatch?
        return vinegar.dump(
            typ, val, tb,
            include_local_traceback=self._config["include_local_traceback"])

    def _unbox_exc(self, raw):  # dispatch?
        return vinegar.load(raw,
                            import_custom_exceptions=self._config["import_custom_exceptions"],
                            instantiate_custom_exceptions=self._config["instantiate_custom_exceptions"],
                            instantiate_oldstyle_exceptions=self._config["instantiate_oldstyle_exceptions"])

    @property
    def root(self):  # serving
        """Fetches the root object (service) of the other party"""
        if self._remote_root is None:
            self._remote_root = self.sync_request(consts.HANDLE_GETROOT)
        return self._remote_root

    def _check_attr(self, obj, name, perm):  # attribute access
        config = self._config
        if not config[perm]:
            raise AttributeError("cannot access %r" % (name,))
        prefix = config["allow_exposed_attrs"] and config["exposed_prefix"]
        plain = config["allow_all_attrs"]
        plain |= config["allow_exposed_attrs"] and name.startswith(prefix)
        plain |= config["allow_safe_attrs"] and name in config["safe_attrs"]
        plain |= config["allow_public_attrs"] and not name.startswith("_")
        has_exposed = prefix and hasattr(obj, prefix + name)
        if plain and (not has_exposed or hasattr(obj, name)):
            return name
        if has_exposed:
            return prefix + name
        if plain:
            return name  # chance for better traceback
        raise AttributeError("cannot access %r" % (name,))

    def _access_attr(self, obj, name, args, overrider, param, default):  # attribute access
        if type(name) is bytes:
            name = str(name, "utf8")
        elif type(name) is not str:
            raise TypeError("name must be a string")
        accessor = getattr(type(obj), overrider, None)
        if accessor is None:
            accessor = default
            name = self._check_attr(obj, name, param)
        return accessor(obj, name, *args)

    @classmethod
    def _request_handlers(cls):  # request handlers
        return {
            consts.HANDLE_CLOSE: cls._handle_close,
            consts.HANDLE_GETROOT: cls._handle_getroot,
            consts.HANDLE_GETATTR: cls._handle_getattr,
            consts.HANDLE_DELATTR: cls._handle_delattr,
            consts.HANDLE_SETATTR: cls._handle_setattr,
            consts.HANDLE_CALL: cls._handle_call,
            consts.HANDLE_CALLATTR: cls._handle_callattr,
            consts.HANDLE_REPR: cls._handle_repr,
            consts.HANDLE_STR: cls._handle_str,
            consts.HANDLE_CMP: cls._handle_cmp,
            consts.HANDLE_HASH: cls._handle_hash,
            consts.HANDLE_INSTANCECHECK: cls._handle_instancecheck,
            consts.HANDLE_DIR: cls._handle_dir,
            consts.HANDLE_PICKLE: cls._handle_pickle,
            consts.HANDLE_DEL: cls._handle_del,
            consts.HANDLE_INSPECT: cls._handle_inspect,
            consts.HANDLE_BUFFITER: cls._handle_buffiter,
            consts.HANDLE_OLDSLICING: cls._handle_oldslicing,
            consts.HANDLE_CTXEXIT: cls._handle_ctxexit,
        }

    def _handle_close(self):  # request handler
        self._cleanup()

    def _handle_getroot(self):  # request handler
        return self._local_root

    def _handle_del(self, obj, count=1):  # request handler
        # print(f'Local dec: {get_id_pack(obj)}, {obj}')
        self._local_objects.decref(get_id_pack(obj), count)

    def _handle_repr(self, obj):  # request handler
        return repr(obj)

    def _handle_str(self, obj):  # request handler
        return str(obj)

    def _handle_cmp(self, obj, other, op='__cmp__'):  # request handler
        # cmp() might enter recursive resonance... so use the underlying type and return cmp(obj, other)
        try:
            return self._access_attr(type(obj), op, (), "_rpyc_getattr", "allow_getattr", getattr)(obj, other)
        except Exception:
            raise

    def _handle_hash(self, obj):  # request handler
        return hash(obj)

    def _handle_call(self, obj, args, kwargs=()):  # request handler
        return obj(*args, **dict(kwargs))

    def _handle_dir(self, obj):  # request handler
        return tuple(dir(obj))

    def _handle_inspect(self, id_pack):  # request handler
        if hasattr(self._local_objects[id_pack], '____conn__'):
            # When RPyC is chained (RPyC over RPyC), id_pack is cached in local objects as a netref
            # since __mro__ is not a safe attribute the request is forwarded using the proxy connection
            # see issue #346 or tests.test_rpyc_over_rpyc.Test_rpyc_over_rpyc
            conn = self._local_objects[id_pack].____conn__
            return conn.sync_request(consts.HANDLE_INSPECT, id_pack)
        else:
            return tuple(get_methods(netref.LOCAL_ATTRS, self._local_objects[id_pack]))

    def _handle_getattr(self, obj, name):  # request handler
        return self._access_attr(obj, name, (), "_rpyc_getattr", "allow_getattr", getattr)

    def _handle_delattr(self, obj, name):  # request handler
        return self._access_attr(obj, name, (), "_rpyc_delattr", "allow_delattr", delattr)

    def _handle_setattr(self, obj, name, value):  # request handler
        return self._access_attr(obj, name, (value,), "_rpyc_setattr", "allow_setattr", setattr)

    def _handle_callattr(self, obj, name, args, kwargs=()):  # request handler
        obj = self._handle_getattr(obj, name)
        return self._handle_call(obj, args, kwargs)

    def _handle_ctxexit(self, obj, exc):  # request handler
        if exc:
            try:
                raise exc
            except Exception:
                exc, typ, tb = sys.exc_info()
        else:
            typ = tb = None
        return self._handle_getattr(obj, "__exit__")(exc, typ, tb)

    def _handle_instancecheck(self, obj, other_id_pack):
        # TODOs:
        #  + refactor cache instancecheck/inspect/class_factory
        #  + improve cache docs

        if hasattr(obj, '____conn__'):  # keep unwrapping!
            # When RPyC is chained (RPyC over RPyC), id_pack is cached in local objects as a netref
            # since __mro__ is not a safe attribute the request is forwarded using the proxy connection
            # relates to issue #346 or tests.test_netref_hierachy.Test_Netref_Hierarchy.test_StandardError
            conn = obj.____conn__
            return conn.sync_request(consts.HANDLE_INSPECT, other_id_pack)
        # Create a name pack which would be familiar here and see if there is a hit
        other_id_pack2 = (other_id_pack[0], other_id_pack[1], 0)
        if other_id_pack[0] in netref.builtin_classes_cache:
            cls = netref.builtin_classes_cache[other_id_pack[0]]
            other = cls(self, other_id_pack)
        elif other_id_pack2 in self._netref_classes_cache:
            cls = self._netref_classes_cache[other_id_pack2]
            other = cls(self, other_id_pack2)
        else:  # might just have missed cache, FIX ME
            return False
        return isinstance(other, obj)

    def _handle_pickle(self, obj, proto):  # request handler
        if not self._config["allow_pickle"]:
            raise ValueError("pickling is disabled")
        return bytes(pickle.dumps(obj, proto))

    def _handle_buffiter(self, obj, count):  # request handler
        return tuple(itertools.islice(obj, count))

    def _handle_oldslicing(self, obj, attempt, fallback, start, stop, args):  # request handler
        try:
            # first try __xxxitem__
            getitem = self._handle_getattr(obj, attempt)
            return getitem(slice(start, stop), *args)
        except Exception:
            # fallback to __xxxslice__. see issue #41
            if stop is None:
                stop = sys.maxsize
            getslice = self._handle_getattr(obj, fallback)
            return getslice(start, stop, *args)
