Module vpe.mapping
==================

.. py:module:: vpe.mapping

Python support for key sequence mapping.

This module provides support for mapping key sequences to Python function
calls.

MapCallback
-----------

.. py:class:: vpe.mapping.MapCallback(...)

    .. parsed-literal::

        MapCallback(
            func,
            \*,
            py_args=(),
            py_kwargs={},
            vim_exprs=(),
            pass_bytes=False,
            \*\*kwargs)

    Wrapper for a function to be invoked by a key mapping.

    This extends the core `Callback` to provide a `MappingInfo` as the first
    positional argument.

    **Methods**

        .. py:method:: vpe.mapping.MapCallback.get_call_args()

            Get the Python positional and keyword arguments.

            This makes the first positional argument a `MappingInfo` instance.

MappingInfo
-----------

.. py:class:: vpe.mapping.MappingInfo(mode: str,keys: str)

    Information passed to a key mapping callback handler.

    The initialisation parameters are made available as attributes.

    **Attributes**

        .. py:attribute:: vpe.mapping.MappingInfo.end_cursor

            When mode=="visual", a tuple (line, column) of the selection
            end. Both values are 1-based. Will be (-1, -1) when not
            applicable.

        .. py:attribute:: vpe.mapping.MappingInfo.keys

            The sequence of keys that triggered the mapping.

        .. py:attribute:: vpe.mapping.MappingInfo.mode

            The mode in which the mapping was triggered (normal, visual,
            op-pending or insert).

        .. py:attribute:: vpe.mapping.MappingInfo.start_cursor

            When mode=="visual", a tuple (line, column) of the selection
            start. Both values are 1-based. Will be (-1, -1) when not
            applicable.

        .. py:attribute:: vpe.mapping.MappingInfo.vmode

            The visual mode (character, line or block). Will be ``None``
            when not applicable.

    **Properties**

        .. py:method:: vpe.mapping.MappingInfo.line_range() -> Optional[Tuple[int, int]]
            :property:

            The line range, if visual mode was active.

            This is a Python style range.

imap
----

.. py:function:: vpe.mapping.imap(...)

    .. parsed-literal::

        imap(
            keys: str,
            func: typing.Callable,
            \*,
            buffer: bool = True,
            silent: bool = True,
            unique: bool = False,
            nowait: bool = False,
            command: bool = False,
            args=(),
            kwargs: Optional[dict] = None)

    Set up an insert mapping that invokes a Python function.

    See `map` for argument details.

map
---

.. py:function:: vpe.mapping.map(...)

    .. parsed-literal::

        map(
            mode: str,
            keys: str,
            func: typing.Callable,
            \*,
            buffer: bool = True,
            silent: bool = True,
            unique: bool = False,
            nowait: bool = False,
            command: bool = False,
            args=(),
            kwargs: Optional[dict] = None,
            vim_exprs: Tuple[str, ...] = ())

    Set up a key mapping that invokes a Python function.

    By default, the effective map command has the form:

       {m}noremap <buffer> <silent> keys ...

    Where {m} is one of n, x, o, i.

    The noremap form is always used.

    The first argument passed to the mapped function is a `MappingInfo` object.
    Additional arguments can be speficied using *args* and *kwargs*.

    For convenience, mode specific versions are provided (`nmap`, `xmap`,
    `omap` and `imap`). See those for details of what he mapped function can
    do. It is recommended that these mode specific versions are use in
    preference to this function.

    **Parameters**

    .. container:: parameters itemdetails

        *mode*: str
            A string defining the mode in which the mapping occurs. This
            should be one of: normal, visual, op-pending, insert, command.
        *keys*: str
            The key sequence to be mapped.
        *func*: typing.Callable
            The Python function to invoke for the mapping.
        *buffer*: bool
            Use the <buffer> special argument. Defaults to True.
        *silent*: bool
            Use the <silent> special argument. Defaults to True.
        *unique*: bool
            Use the <unique> special argument. Defaults to False.
        *nowait*: bool
            Use the <nowait> special argument. Defaults to False.
        *command*: bool
            Only applicable to insert mode. If true then the function
            is invoked from the command prompt and the return value is not
            used. Otherwise (the default) the function should return the
            text to be inserted.
        *args*
            Additional arguments to pass to the mapped function.
        *kwargs*: typing.Optional[dict]
            Additional keyword arguments to pass to the mapped function.
        *vim_exprs*: typing.Tuple[str, ...]
            Vim expressions to be evaluated and passed to the callback
            function, when the mapping is triggered.

nmap
----

.. py:function:: vpe.mapping.nmap(...)

    .. parsed-literal::

        nmap(
            keys: str,
            func: typing.Callable,
            \*,
            buffer: bool = True,
            silent: bool = True,
            unique: bool = False,
            nowait: bool = False,
            args=(),
            kwargs: Optional[dict] = None)

    Set up a normal mode  mapping that invokes a Python function.

    See `map` for argument details.

omap
----

.. py:function:: vpe.mapping.omap(...)

    .. parsed-literal::

        omap(
            keys: str,
            func: typing.Callable,
            \*,
            buffer: bool = True,
            silent: bool = True,
            unique: bool = False,
            nowait: bool = False,
            args=(),
            kwargs: Optional[dict] = None)

    Set up am operator-pending mode mapping that invokes a Python function.

    See `map` for argument details.

xmap
----

.. py:function:: vpe.mapping.xmap(...)

    .. parsed-literal::

        xmap(
            keys: str,
            func: typing.Callable,
            \*,
            buffer: bool = True,
            silent: bool = True,
            unique: bool = False,
            nowait: bool = False,
            args=(),
            kwargs: Optional[dict] = None)

    Set up a visual mode mapping that invokes a Python function.

    See `map` for argument details.