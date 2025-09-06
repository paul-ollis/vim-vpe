"""Very common code."""
from __future__ import annotations
# pylint: disable=too-many-lines

import io
import pprint
import re
import traceback
import weakref
from functools import partial
from typing import (
    Any, Callable, ClassVar, Dict, Final, List, Optional, Tuple, Union)

import vim as _vim
from vpe import utils
from vpe.utils import QuietWeakMethod

__api__ = [
    'Callback',
    'CommandCallback',
    'vim_command',
    'vim_eval',
]
__all__ = [
    'build_dict_arg',
    'Callback',
    'call_soon',
    'call_soon_once',
    'CommandInfo',
    'OneShotTimer',
    'suppress_vim_invocation_errors',
    'Timer',
    'vim_command',
    'VimError',
]
_NOT_PROVIDED = object()
RET_VAR = 'g:VPE_ret_value'
_vim.vars[RET_VAR] = ''
id_source = utils.uid_source


def _create_vim_function(name: str) -> Optional[_vim.Function]:
    """Create a wrapped Vim function using _vim.Function.

    :name: The Vim function name.
    :return: The wrapped function or ``None`` if the function does not exist in
             this version of Vim.
    """
    if _vim.eval(f'exists("*{name}")') != '0':
        return Function(name)

    return None                                           # pragma: unreachable


def register_wrapper(vim_type, wrapper):
    """Add an entry to the set of wrapped Vim module types."""
    _wrappers[vim_type] = wrapper


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
        return exc_val is not None and isinstance(exc_val, _vim.error)


# Context manager used to prevent logging of Vim function call errors.
suppress_vim_invocation_errors = _ErrorSuppressor()


class Function:
    """Wrapper around a vim.Function.

    This provides some wrapping and decoding of return types.
    """
    def __init__(self, name_or_func, **kwargs):
        assert isinstance(name_or_func, str) or callable(name_or_func)
        if callable(name_or_func):
            self._vim_function = name_or_func
            self._name = name_or_func.__name__
        else:
            self._vim_function = _vim.Function(name_or_func, **kwargs)
            self._name = name_or_func

    @property
    def name(self) -> str:
        """The name of this function."""
        return self._name

    # pylint: disable=too-few-public-methods
    def __call__(self, *args, **kwargs):
        # pylint: disable=condition-evals-to-constant
        # pylint: enable=condition-evals-to-constant

        # This can be useful for debugging, but be careful which functions are
        # selected.
        #-if 'extend' in self.name:
        #-    # pylint: disable=simplifiable-condition
        #-    call_soon(print, f'Function.__call__: {self.name}'
        #-           f' vim.state()={_vim.eval("state()")}')
        #-    for i, a in enumerate(args):
        #-        call_soon(print, f' args[{i}] ={a!r}')

        if suppress_vim_invocation_errors.active:
            v = self._vim_function(*args, **kwargs)  # pylint: disable=no-member
        else:
            try:
                # pylint: disable=no-member
                v = self._vim_function(*args, **kwargs)
            except Exception as e:
                args_lines = pprint.pformat(args).splitlines()
                kwargs_lines = pprint.pformat(kwargs).splitlines()
                s = [f'VPE: Function[{self._name}].__call__ failed: {e}']
                s.append(f'    self.args={self._vim_function.args}')
                s.append(f'    self.self={self._vim_function.self}')
                s.append(f'    args={args_lines[0]}')
                for line in args_lines[1:]:
                    s.append(f'         {line}')
                s.append(f'    kwargs={kwargs_lines[0]}')
                for line in kwargs_lines[1:]:
                    s.append(f'           {line}')
                s.append(f'    vim.state()={_vim.eval("state()")}')
                call_soon(print, '\n'.join(s))
                if isinstance(e, _vim.error):
                    raise VimError(e) from None
                raise                                        # pragma: no cover
        if isinstance(v, bytes):
            try:
                return v.decode()
            except UnicodeError:                             # pragma: no cover
                return v
        return wrap_or_decode(v)


class VimError(_vim.error, Exception):
    """A parsed version of vim.error.

    VPE code raises this in place of the standard vim.error exception. It is
    a subclass of vim.error, so code that handles vim.error will still work
    when converted to use the `vpe.vim` object.

    This exception attempts to parse the Vim error string to provide additional
    attributes:

    @command: The name of the Vim command that raised the error. This may be
              an empty string.
    @code:    The error code. This will be zero if parsing failed to extract
              the code.
    @message: The message part, after extracting the command, error code and
              'Vim' prefix. If parsing completely fails then is simply the
              unparsed message.
    """
    command: str
    code: int
    message: str

    def __init__(self, error: _vim.error):
        super().__init__(str(error))
        self.message: str
        self.command: str = ''
        self.code: int = 0
        pat = r'''(?x)
            Vim                           # Common prefix.
            (?:
                \( (?P<command> \w+ ) \)  # May have command in parentheses.
            ) ?
            :
            (?:
                E (?P<code> \d{1,4} )     # May have an error code.
            :
            ) ?
            [ ] (?P<message> .* )         # Space then free form message.
        '''
        m = re.match(pat, str(error))
        if m:
            code = m.group('code')
            self.code = int(code) if code else 0
            self.command = m.group('command') or ''
            self.message = m.group('message')
        else:
            self.message = str(error)


def _decode_proxy(s):
    name, _, value = s.partition(' ')
    name = name[1:]
    value = value[:-1]
    if name in ('tabpage', 'vim.tabpage'):
        return _vim.TabPage(value)                           # pragma: no cover
    if name in ('window', 'vim.window'):
        return _vim.Window(value)                            # pragma: no cover
    if name in ('buffer', 'vim.buffer'):
        return _vim.Buffer(value)                            # pragma: no cover
    if name in ('vim.options',):
        return _vim.options                                  # pragma: no cover
    return None


class Proxy:
    """Base for proxy classes.

    Subclasses must support the following protocol:

        - The proxied object is avalable as an attribute or property called
          '_proxied'.

        - May provide a _resolve_item method. Typically this will undo any
          proxy wrapping.

        - May provide a _wrap_or_decode method. Typically this is used to wrap
          the value in a proxy or convert bytes to strings.

    IMPORTANT
        This base class overrides __setattr__. Subclasses should use
        self.__dict__ to explicitly set attributes (*e.g.* the _proxied
        attribute).
    """
    _writeable: set = set()

    def __init__(self, obj=None):
        super().__init__()
        if obj is not None:
            self.__dict__['_proxied'] = self._resolve_item(obj)

    def __getstate__(self):
        """Trivial pickle support - just for testing."""
        state = self.__dict__.copy()
        if '_proxied' in state:
            state['_proxied'] = repr(state['_proxied'])
        return state

    def __setstate__(self, state):
        """Trivial pickle support - just for testing."""
        if '_proxied' in state:
            state['_proxied'] = _decode_proxy(state['_proxied'])
        return self.__dict__.update(state)

    def __getattr__(self, name):
        return self._wrap_or_decode(getattr(self._proxied, name), name)

    def __setattr__(self, name, value):
        setter = getattr(self, f'_set__{name}', None)
        if setter is not None:
            setter(value)
            return

        if name in self._writeable:
            setattr(self._proxied, name, value)
        elif name in self.__dict__:
            self.__dict__[name] = value
        elif name == '__dict__':
            super().__setattr__('__dict__', value)           # pragma: no cover
        else:
            prop = getattr(self.__class__, name, None)
            if isinstance(prop, property):
                fset = getattr(prop, 'fset', None)
                if fset is not None:                         # pragma: no cover
                    fset(self, value)
                    return

            raise AttributeError(
                f"Can't set attribute {name!r} for {self.__class__.__name__}")

    def _resolve_item(self, item: Any) -> Any:
        """Resolve an item.

        Recursivley drill down to the ultimate proxied object for the *item*.

        :item: The item to resolve.
        :return:
            The proxied object or the *item* itself.
        """
        try:
            return self._resolve_item(getattr(item, '._proxied'))
        except AttributeError:
            return item

    def _wrap_or_decode(self, value, _name=None):
        """Optionally wrap an item.

        This default implementation uses a common wrapping function.
        """
        return wrap_or_decode(value)


class ContainerProxy(Proxy):
    """Base for containers that support iteration and have a length.

    This is not intended to be instantiated.
    """
    def __iter__(self):
        for item in self._proxied:
            yield self._wrap_or_decode(item)

    def __len__(self):
        return len(self._proxied)


class ImmutableSequenceProxy(ContainerProxy):
    """Base for sequence style proxy classes.

    This wraps things like the window and tab page lists.
    """
    # pylint: disable=too-few-public-methods
    def __getitem__(self, index_or_slice: int | slice) -> Any:
        return self._wrap_or_decode(self._proxied[index_or_slice])


class MutableSequenceProxy(ImmutableSequenceProxy):
    """A mutable squence proxy.

    This wraps things like buffers and Vim lists.
    """
    def __setitem__(self, slice_or_index, value):
        self._proxied.__setitem__(slice_or_index, value)

    def __delitem__(self, slice_or_index):
        self._proxied.__delitem__(slice_or_index)

    def insert(self, index: int, value: Any):
        """Insert a value as a given index.

        :index: The index for the insertion.
        :value: The value to insert.
        """
        self._proxied[index:index] = [value]


class MutableMappingProxy(ContainerProxy):
    """A mutable mapping proxy for Vim objects.

    This wraps things like Vim dictionaries and variables.
    """
    def __getitem__(self, key: str) -> Any:
        return self._wrap_or_decode(self._proxied[key])

    def __setitem__(self, key: str, value):
        self._proxied[key] = value

    def __delitem__(self, key: str):
        del self._proxied[key]

    def keys(self) -> List[str]:
        """The mapping's keys, each one decoded to a string."""
        return [self._wrap_or_decode(k) for k in self._proxied.keys()]

    # TODO: This does not wrap the returned values.
    def values(self) -> List[Any]:
        """The maping's values, each one wrapped or decoded."""
        return [self._wrap_or_decode(v) for v in self._proxied.values()]

    # TODO: This does not wrap the returned values.
    def items(self):
        """The maping's (key, value) pairs, each one wrapped or decoded."""
        wrap = self._wrap_or_decode
        return [(wrap(k), wrap(v)) for k, v in self._proxied.items()]

    def get(self, key: str, default: Optional[Any] = None):
        """Lookup a value from the mapping."""
        return self._wrap_or_decode(self._proxied.get(key, default), key)

    def pop(self, key, default=_NOT_PROVIDED):
        """Remove en entry and return is value.

        :key:    The key of the item to remove.
        :return:
            The removed item (if found) or the default (if provided). The
            returned value may be decoded or wrapped.
        :raise KeyError:
            if key is not found and no default provided.
        """
        if default is _NOT_PROVIDED:
            return self._wrap_or_decode(self._proxied.pop(key), key)
        return self._wrap_or_decode(self._proxied.pop(key, default), key)

    def popitem(self) -> Tuple[str, Any]:
        """Pop a random (key, value pair) from the mapping."""
        key, value = self._proxied.popitem()
        return self._wrap_or_decode(key), self._wrap_or_decode(value, key)

    def has_key(self, key: Any) -> bool:
        """Test whether a key is present in the mapping.

        :key: The key to look for.
        """
        return key in self._proxied

    def __contains__(self, key):
        return key in self._proxied

    def __iter__(self):
        """Correctly support 'for v in dict'.

        This is really working around a bug in earlier versions of vim.
        """
        return iter(self.keys())


class Callback:
    """Wrapper for a function to be called from Vim.

    This encapsulates the mechanism used to arrange for a Python function to
    be invoked in response to an event in the 'Vim World'. A Callback stores
    the Python function together with an ID that is uniquely associated with
    the function (the UID). If, for example this wraps function 'spam' giving
    it UID=42 then the Vim script code:
    ::

        :call VPE_Call(42, 'hello', 123)

    will result in the Python function 'spam' being invoked as:<py>:

        spam('hello', 123)

    The way this works is that the VPE_Call function first stores the UID
    and arguments in the global Vim variable _vpe_args_ in a dictionary
    as:<py>:

        {
            'uid': 42,
            'args': ['hello', 123]
        }

    Then it calls this class's `invoke` classmethod::

        return py3eval('vpe.Callback.invoke()')

    The `invoke` class method extracts the UID and uses it to find the
    Callback instance.

    Note that a strong reference to each `Callback` instance is automatically
    stored, but only while a strong reference to the function exists.

    :func:        The Python function or method to be called back.
    :@py_args:    Addition positional arguments to be passed to *func*.
    :@py_kwargs:  Additional keyword arguments to be passed to *func*.
    :@vim_exprs:  Expressions used as positional arguments for the VPE_Call
                  helper function.
    :@pass_bytes: If true then vim byte-strings will not be decoded to Python
                  strings.
    :@once:       If True then the callback will only ever be invoked once.
    :cleanup:     If supplied then this is callable taking no arguments.
                  It is invoked to perform any special clean up actions when
                  the function is no longer referenced.
    :@meta:       Arbitrary meta-data to be stored in the Callback's `meta`
                  attribute.
    :kwargs:      Additional info to store with the callback. This is used
                  by subclasses - see 'MapCallback' for an example.

    @uid:         The unique ID for this wrapping. It is the string form of an
                  integer.
    @call_count:  The number of times the wrapped function or method has been
                  invoked.
    @callbacks    A class level mapping from `uid` to `Callback` instance. This
                  is used to lookup the correct function during the execution
                  of VPE_Call.
    """
    # pylint: disable=too-many-instance-attributes

    #: The name of the Vim world function that is used as the Vim callback.
    vim_func = 'VPE_Call'

    def __init__(
            self,
            func: Callable[[...], None],
            *,
            py_args: tuple[Any, ...] = (),
            py_kwargs: dict[str, Any] | None = None,
            vim_exprs: tuple[Any, ...] = (),
            pass_bytes: bool = False,
            once: bool = False,
            cleanup: Callable[[], None] | None = None,
            meta: Any | None = None,
            **kwargs):
        # pylint: disable=too-many-arguments
        uid = self.uid = id_source.alloc()
        #-log_death = partial(
        #-    print, f'uid={uid} is dead! {func}({py_args} {py_kwargs})')
        def log_death():
            pass
        func_reference_store.add(
            uid, func, cleanup=Cleaner(cleanup, log_death), meta=self)

        self.vim_exprs = vim_exprs
        self.py_args = py_args
        self.py_kwargs = {} if py_kwargs is None else py_kwargs.copy()
        self.extra_kwargs = kwargs
        self.pass_bytes = pass_bytes
        self.once = once
        self.call_count = 0
        self.meta = meta
        try:
            self.func_name = func.__name__
            try:
                obj = func.__self__
            except AttributeError:
                pass
            else:
                self.func_name = f'{obj.__class__.__name__}.{self.func_name}'
        except AttributeError:                               # pragma: no cover
            self.func_name = str(func)

    def get_call_args(self, _vpe_args: Dict[str, Any]):
        """Get the Python positional and keyword arguments.

        This may be over-ridden by subclasses.

        :_vpe_args: The dictionary passed from the Vim domain.
        """
        return self.py_args, self.py_kwargs

    def invoke_cb(self, func: Callable, vpe_args: dict):
        """Invoke this Callback.

        This invokes the function as:<py>:

            func(*args, *vim_args, **kwargs)

        Where args and kwargs are those provided when this instance was
        created. The vim_args arr the 'args' from the vpe_args dictionary.

        :vpe_args:
            A dictionary containing:

            uid
                The unique ID that is used to find the correct `Callback`
                instance.
            args
                Any additional arguments passed to the callback by Vim.
        """
        if self.once and self.call_count > 0:                # pragma: no cover
            # This handles older version of Vim that do not support ++once for
            # auto-commands.
            return 0

        # Get the arguments supplied from the 'Vim World' plus the python
        # positional and keyword arguments. The invoke the wrapped function or
        # method.
        coerce = partial(coerce_arg, keep_bytes=self.pass_bytes)
        vim_args = [coerce(arg) for arg in vpe_args.pop('args')]
        args, kwargs = self.get_call_args(vpe_args)
        ret = func(*args, *vim_args, **kwargs)
        self.call_count += 1

        # Make some attempt to avoid returning unconvertable values back to the
        # 'Vim World'. This reduces the display of annoying messages.
        if ret is None:
            ret = 0
        return ret

    @classmethod
    def invoke(cls) -> Any:
        """Invoke a particular callback function instance.

        This is invoked from the 'Vim World' by VPE_Call. The global Vim
        dictionary variable _vpe_args_ will have been set up to contain 'uid'
        and 'args' entries. The 'uid' is used to find the actual `Callback`
        instance and the 'args' is a sequence of Vim values, which are passed
        to the callback as positional arguments.

        The details are store in the Vim global variable ``_vpe_args_``, which
        is a dictionary containing:

        uid
            The unique ID that is used to find the correct `Callback` instance.
        args
            Any additional arguments passed to the callback by Vim.

        It is possible that there is no instance for the given `uid`. In that
        case a message is logged, but no other action taken.

        :return:
            Normally the return value of the invoked function. If the callback
            is dead then the value is zero and if an exception is raised then
            the value is -1.
        """
        wod = wrap_or_decode
        vpe_args = dict(
            (wod(k), wod(v)) for k, v in _vim.vars['_vpe_args_'].items())
        uid = vpe_args.pop('uid')
        func, cb = func_reference_store.retrieve(uid)
        if func is None:
            return -1

        try:
            return cb.invoke_cb(func, vpe_args)

        except Exception as e:                   # pylint: disable=broad-except
            # Log any exception, but do not allow it to disrupt normal Vim
            # behaviour.
            s = [f'{e.__class__.__name__} invocation failed: {e}']
            s.append(cb.format_call_fail_message())
            f = io.StringIO()
            traceback.print_exc(file=f)
            s.append(f.getvalue())
            call_soon(print, '\n'.join(s))

        return -1

    def as_invocation(self):
        """Format an expression of the form 'VPE_Call("42", ...)'.

        The result is a valid Vim script expression.
        """
        vim_exprs = [quoted_string(self.uid), quoted_string(self.func_name)]
        for a in self.vim_exprs:
            if isinstance(a, str):
                vim_exprs.append(quoted_string(a))
            else:
                vim_exprs.append(str(a))
        return f'{self.vim_func}({", ".join(vim_exprs)})'

    def as_call(self):
        """Format a command of the form 'call VPE_Call("42", ...)'.

        The result can be used as a colon prompt command.
        """
        return f'call {self.as_invocation()}'

    # TODO: This form ignores the vim_exprs.
    def as_vim_function(self):
        """Create a ``vim.Function`` that will route to this callback."""
        return _vim.Function(
            f'g:{self.vim_func}', args=[self.uid, self.func_name])

    def format_call_fail_message(self):
        """Generate a message to give details of a failed callback invocation.

        This is used when the `Callback` instance exists, but the call raised
        an exception.
        """
        s = [f'Function {self.func_name}']
        s.append(f'    vim_exprs={self.vim_exprs}')
        s.append(f'    py_args={self.py_args}')
        s.append(f'    py_kwargs={self.py_kwargs}')
        return '\n'.join(s)

    def __repr__(self) -> str:
        func, _ = func_reference_store.retrieve(self.uid)
        dead = ' dead!' if func is None else ''
        return f'<{self.__class__.__name__}:{self.func_name}{dead}>'


class CommandInfo:                     # pylint: disable=too-few-public-methods
    """Information passed to a user command callback handler.

    @line1: The start line of the command range.
    @line2: The end line of the command range.
    @range: The number of items in the command range: 0, 1 or 2 Requires at
            least vim 8.0.1089; for earlier versions this is fixed as -1.
    @count: Any count value supplied (see :vim:`command-count`).
    @bang:  True if the command was invoked with a '!'.
    @mods:  The command modifiers (see :vim:`:command-modifiers`).
    @reg:   The optional register, if provided.
    """
    def __init__(
            self, line1: int, line2: int, range: int, count: int, bang: bool,
            mods: str, reg: str):
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        # pylint: disable=redefined-builtin
        self.line1 = line1
        self.line2 = line2
        self.range = range
        self.count = count
        self.bang = bang
        self.mods = mods
        self.reg = reg


class CommandCallback(Callback):
    """Wrapper for a function to be invoked by a user defined command.

    This extends the core `Callback` to provide a `CommandInfo` as the first
    positional argument.

    @pass_info: If True, provide a MappingInfo object as the first argument to
    """
    vim_func = 'VPE_CmdCall'

    def __init__(self, *args, **kwargs):
        self.pass_info = kwargs.pop('pass_info', False)
        super().__init__(*args, **kwargs)

    def get_call_args(self, vpe_args: Dict[str, Any]):
        """Get the Python positional and keyword arguments.

        This makes the first positional argument a `CommandInfo` instance,
        unless `pass_info` has been set false.
        """
        vpe_args['bang'] = bool(vpe_args['bang'])
        if self.pass_info:
            py_args = CommandInfo(**vpe_args), *self.py_args
        else:
            py_args = self.py_args
        return py_args, self.py_kwargs


class Timer(Callback):
    """Pythonic way to use Vim's timers.

    This can be used as a replacement for the vim functions: timer_start,
    timer_info, timer_pause, timer_stop.

    An example of usage:<py>:

        def handle_expire(t):
            print(f'Remaining repeats = {t.repeat}')

        # This will cause handle_expire to be called twice. The output will be:
        #     t.repeat=2
        #     t.repeat=1
        t = Timer(ms=100, handle_expire, repeat=2)

    The status of a timer can be queried using the properties `time`, `repeat`,
    `remaining` and `paused`. The methods `pause`, `stop` and `resume` allow
    an active timer to be controlled.

    A timer with ms == 0 is a special case. It is used to schedule an action to
    occur as soon as possible once Vim is waiting for user input. Consequently
    the repeat argument is forced to be 1 and the pass_timer argument is forced
    to be ``False``.

    :ms:          The timer's interval in milliseconds. The value ``int(ms)``
                  is used.
    :func:        The function to be invoked when the timer fires. This is
                  called with the firing `Timer` instance as the only
                  parameter.
    :repeat:      How many times to fire. This defaults to a single firing.
    :pass_timer:  Set this false to prevent the timer being passed to func.
    :@meta:       Arbitrary meta-data to be stored in the Callback's `meta`
                  attribute.
    :@args:       Optional positional arguments to pass to func.
    :@kwargs:     Optional keyword arguments to pass to func.

    @fire_count:  This increases by one each time the timer's callback is
                  invoked.
    @dead:        This is set true when the timer is no longer active because
                  all repeats have occurred or because the callback function is
                  no longer available.
    """
    def __init__(
            self,
            ms : int | float,
            func: Callable[[...], None],
            *,
            repeat: int | None = None,
            pass_timer: bool = True,
            meta: Any | None = None,
            args=(),
            kwargs=None,
        ):
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=too-many-arguments
        def cleanup():
            self.dead = True

        super().__init__(
            func, py_args=args, py_kwargs=kwargs, meta=meta, cleanup=cleanup)
        repeat = 1 if repeat is None else repeat
        self.ms = int(ms)
        if self.ms == 0:
            # This is for a delayed-until-vim-mainloop call. Make sure it only
            # runs once.
            repeat = 1
            pass_timer = False
        if pass_timer:
            self.py_args = (self,) + self.py_args
        vopts = {'repeat': repeat}
        self._id = _timer_start(self.ms, self.as_vim_function(), vopts)
        self.fire_count = 0
        self.dead = False

    @property
    def id(self) -> int:
        """The ID of the underlying vim timer."""
        return self._id

    @property
    def time(self) -> int:
        """The time value used to create the timer."""
        return self._get_info('time')

    @property
    def repeat(self) -> int:
        """The number of times the timer will still fire.

        Note that prior to Vim patch 8.2.3768 this was 1 greater that one might
        expect. Now Vim's ``timer_info()`` returns the expected value except
        during the final callback, when we get ``None``. This is non-Pythonic,
        so ``None`` is converted to zero.
        """
        v = self._get_info('repeat')
        return 0 if v is None else v

    @property
    def remaining(self) -> int:
        """The time remaining (ms) until the timer will next fire."""
        return self._get_info('remaining')

    @property
    def paused(self) -> bool:
        """True if the timer is currently paused."""
        return bool(self._get_info('paused'))

    def _get_info(self, name):
        info = _timer_info(self.id)
        return info[0][name] if info else None

    def stop(self):
        """Stop the timer.

        This invokes vim's timer_stop function.
        """
        _timer_stop(self.id)
        self.finish()

    def pause(self):
        """Pause the timer.

        This invokes vim's timer_pause function.
        """
        _timer_pause(self.id, True)

    def resume(self):
        """Resume the timer, if paused.

        This invokes vim's timer_pause function.
        """
        _timer_pause(self.id, False)

    def invoke_cb(self, func: Callable, vpe_args: dict):
        """Invoke the callback as a result of the timer firing."""
        vpe_args['args'] = vpe_args['args'][1:]     # Drop the unused timer ID.
        self.fire_count += 1
        try:
            super().invoke_cb(func, vpe_args)
        finally:
            if self.repeat == 0:
                self.finish()

    def finish(self):
        """Take action when a timer is finished."""
        self.dead = True
        func_reference_store.drop(self.uid)


class OneShotTimer(Timer):
    """A version of `Timer` that can be used 'set-and-forget'.

    This version makes sure that a reference to the function and the
    `OneShotTimer` instance is saved until the timer fires. This means that
    this type of code will work:<py>:

        def one_shot_example():
            def fire():
                print('Bang!')
            OneShotTimer(1000, fire)

    The callback function is invoked without arguments.
    """
    def __init__(self, ms : int, func: Callable[[...], None]):
        super().__init__(ms, func, meta=func)

    def invoke_cb(self, func: Callable, vpe_args: dict):
        """Invoke the callback as a result of the timer firing."""
        super().invoke_cb(func, vpe_args)

        # Drop reference to the function allowing automatic cleanup to kick in.
        self.meta = None


class Cleaner:
    """An object that performs cleanup operations."""

    def __init__(self, *funcs: Callable[[None], None] | None | Cleaner):
        self.cleanups = []
        for func in funcs:
            if func is not None:
                self.cleanups.append(func)

    def __call__(self) -> None:
        for func in self.cleanups:
            try:
                func()
            except Exception as e:                           # pragma: no cover
                call_soon(print, f'Cleanup failure for {func}: {e}')


class func_reference_store:
    """A weakly referenced function store, with automatic cleanup.

    This holds weak references to functions/methods and performs cleanup
    operations when a referenced function is about to be finalized.
    """
    registrations: Final[ClassVar[
        dict[str, tuple[weakref.ref, Callable[[], None], Any]]]] = {}

    @classmethod
    def add(
            cls,
            uid: str,
            func: Callable | Callback,
            cleanup: Callable[[], None],
            meta: Any = None,
        ) -> None:
        """Add an object, storing a weak reference and cleanup function.

        :uid:     The unique ID for this stored object.
        :func:    The function/method, which will be weakly referenced.
        :cleanup: A function invoked if the weak reference to the function
                  dies.
        :meta:    Any additional data to be stored against this UID.
        """
        try:
            ref = QuietWeakMethod(func, partial(cls.handle_finalize, uid))
        except TypeError:
            ref = weakref.ref(func, partial(cls.handle_finalize, uid))
        cls.registrations[uid] = ref, cleanup, meta

    @classmethod
    def drop(cls, uid: str) -> None:
        """Drop the entry for a given UID.

        This removes the entry and invokes any clean up actions.
        """
        ref, _cleanup, _meta = cls.registrations.get(uid, (None, None, None))
        if ref is not None:
            cls.handle_finalize(uid, None)

    @classmethod
    def retrieve(cls, uid: str) -> tuple[Callable, Any] | tuple[None, None]:
        """Retrieve a stored object."""
        ref, _cleanup, meta = cls.registrations.get(uid, (None, None, None))
        if ref is None:
            return None, None

        func = ref()
        if func is None:
            cls.handle_finalize(uid, None)
            return None, None
        else:
            return func, meta

    @classmethod
    def handle_finalize(cls, uid: str, _ref: weakref.ref | None) -> None:
        """Handle finalization of a stored object."""
        dead_ref, cleanup, _meta = cls.registrations.pop(
            uid, (None, None, None))
        if dead_ref is not None:
            if not utils.exiting:
                # print(f'Dead function detected {uid} {_meta=}')
                if cleanup is not None:
                    cleanup()

    @classmethod
    def callback_count(cls) -> int:
        """Count the number of callbacks stored."""
        n = 0
        for ref, _, meta in cls.registrations.values():
            if ref() is not None and isinstance(meta, Callback):
                n += 1
        return n


def invoke_vim_function(func: Callable, *args) -> Any:
    """Invoke a Vim function, converting the vim.error to VimError.

    :func:   The function to invoke.
    :args:   Positional arguments, passed unmodified.
    """
    try:
        return func(*args)
    except _vim.error as e:
        raise VimError(e) from None


def coerce_arg(value: Any, keep_bytes=False) -> Any:
    """Coerce a Vim value to a more natural Python value.

    :value:      The value to coerce.
    :keep_bytes: If true then a bytes value is not decoded to a string.
    :return:
        type == bytes
            Unless keep_bytes is set this is decoded to a Python string, if
            possible. If decoding fails, the bytes value is returned.
        type == vim list
            All items in the list are (recursively) coerced.
        type == vim dictionary
            All keys are decoded and all values are (recursively) coerced.
            Failure to decode a key will raise UnicodeError.
    :raise UnicodeError:
        If a dictionay key cannot be decoded.
    """
    # TODO: It seems that this block is never executed any more. Investigate
    #       why rather than simply mark as uncovered.
    if isinstance(value, bytes) and not keep_bytes:          # pragma: no cover
        try:
            return value.decode()
        except UnicodeError:
            return value

    try:
        vim_value = value._proxied  # pylint: disable=protected-access
    except AttributeError:
        vim_value = value

    if isinstance(vim_value, _vim.List):
        return [coerce_arg(el) for el in vim_value]
    elif isinstance(vim_value, _vim.Dictionary):
        return {k.decode(): coerce_arg(v) for k, v in vim_value.items()}
    else:
        return value


def quoted_string(s: str) -> str:
    """Wrap a Vim argument in double quotation marks.

    :s:      The string to be wrapped.
    :return: The string inside double quotes.
    """
    return f'"{s}"'


def build_dict_arg(*pairs: Tuple[str, Any]) -> Dict[str, Any]:
    """Build a dictionary argument for a Vim function.

    This takes a list of name, value pairs and builds a corresponding
    dictionary. Entries with a value of ``None`` are not added to the
    dictionary.

    :pairs: The list if name, value pairs.
    """
    return {name: value for name, value in pairs if value is not None}


def wrap_or_decode(item):
    """Wrap a Vim item with an appropriate VPE wrapper class.

    This is used to wrap vim.buffers, vim.current, *etc*.

    :item: The Vim object to be wrapped.
    :return: An object wrapping the item or, for simple types, the item itself.
    """
    wrapper = _wrappers.get(type(item), None)
    if wrapper is not None:
        return wrapper(item)
    if isinstance(item, bytes):
        try:
            return item.decode()
        except UnicodeError:                                 # pragma: no cover
            return item
    if callable(item):
        return Function(item)
        # return partial(invoke_vim_function, item)
    return item


def prepare_call_soon_timer():
    """Create the call soon timer, if required."""
    if not _scheduled_soon_calls:
        Timer(0, _do_call_soon, pass_timer=False)


def call_soon(func: Callable, *args: Any, **kwargs: Any):
    """Arrange to call a function 'soon'.

    This uses a Vim timer with a delay of 0ms to schedule the function call.
    This means that currently executing Python code will complete *before*
    the function is invoked.

    The function is invoked as:<py>:

        func(*args, **kwargs)

    :func:   The function to be invoked.
    :args:   Positional arguments for the callback function.
    :kwargs: Keyword arguments for the callback function.
    """
    prepare_call_soon_timer()
    _scheduled_soon_calls.append((None, (func, args, kwargs)))


def call_soon_once(
        token: Any, func: Callable, *args: Any, **kwargs: Any):
    """Arrange to call a function 'soon', but only once.

    This is like `call_soon`, but if multiple calls with the same token are
    scheduled then only the first registed function is invoked when Vim's main
    loop regains control.

    :token:  A token that identifies duplicate registered callbacks. This can
             be any object that may be a member of a set, except ``None``.
    :func:   The function to be invoked.
    :args:   Positional arguments for the callback function.
    :kwargs: Keyword arguments for the callback function.
    """
    prepare_call_soon_timer()
    _scheduled_soon_calls.append((token, (func, args, kwargs)))


def _do_call_soon():
    """Invoke any functions scheduled to be called soon.

    Exceptions that occur during invocation are logged but otherwise
    suppressed.
    """
    invoked = set()
    try:
        for token, (func, args, kwargs) in _scheduled_soon_calls:
            if token is None or token not in invoked:
                try:
                    func(*args, **kwargs)
                except Exception:                # pylint: disable=broad-except
                    traceback.print_exc()
                    print('VPE: Exception occurred in callback.')

                invoked.add(token)
    finally:
        _scheduled_soon_calls[:] = []


# A dictionary mapping from various Vim module types to VPE wrapping classes.
_wrappers: Dict[type, Union[type, Callable]] = {}

# A sequence holding functions scheduled using `call_soon`.
_scheduled_soon_calls: List[Tuple[Any, Tuple[Callable, tuple, dict]]] = []

_eval_func = _vim.Function('eval')
vim_command = partial(invoke_vim_function, _vim.command)
vim_simple_eval = partial(invoke_vim_function, _vim.eval)
vim_eval = partial(invoke_vim_function, _eval_func)
_timer_start = _create_vim_function('timer_start')
_timer_info = _create_vim_function('timer_info')
_timer_stop = _create_vim_function('timer_stop')
_timer_pause = _create_vim_function('timer_pause')
_timer_stopall = _create_vim_function('timer_stopall')
