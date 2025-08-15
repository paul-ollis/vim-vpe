"""The ubiquitous utility module."""
from __future__ import annotations

import atexit
import weakref

#: A flag that is set once Vim is exiting.
exiting: bool = False


class UIDSource:
    """A source of unique IDs.

    This provides unique IDs as string representations of integers.
    """

    def __init__(self):
        self.n = 1000

    def alloc(self) -> str:
        """Allocate the next available ID."""
        v = str(self.n)
        self.n += 1
        return v

    def prev_id(self, count: int = 0) -> str:
        """Provide a previously allocated UID.

        This is really only here for testing. Do not use in normal code.

        :count: How far back to look in the UID history.
        """
        return str(self.n - 1 - count)


class QuietWeakMethod(weakref.ref):
    """A quiet version of weakref.WeakMethod.

    The standard library version can cause ignored exception 'noise' when Vim
    exits. This is a minimal copy of the standard library code with suitable
    modifications.
    """
    __slots__ = "_func_ref", "_meth_type", "_alive", "__weakref__"

    def __new__(cls, meth, callback=None):
        try:
            obj = meth.__self__
            func = meth.__func__
        except AttributeError:
            raise TypeError('') from None

        def _cb(arg):
            self = self_wr()
            if self is not None:
                # pylint: disable=protected-access
                self._alive = False
                if callback is not None:
                    callback(self)

        self = weakref.ref.__new__(cls, obj, _cb)
        self._func_ref = weakref.ref(func, _cb)
        self._meth_type = type(meth)
        self._alive = True
        self_wr = weakref.ref(self)
        return self

    def __call__(self):
        obj = super().__call__()
        func = self._func_ref()
        if obj is None or func is None:
            return None
        return self._meth_type(func, obj)


def _note_exit() -> None:
    global exiting                           # pylint: disable=global-statement

    exiting = True                                           # pragma: no cover


# The one and only UIDSource.
uid_source = UIDSource()

# Set the exiting flag using `atexit`.
atexit.register(_note_exit)
