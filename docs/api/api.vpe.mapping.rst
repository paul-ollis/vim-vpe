Module vpe.mapping
==================


.. py:module:: mapping

Python support for key sequence mapping.

This module provides support for mapping key sequences to Python function
calls.

.. rubric:: KeyHandler

.. py:class:: KeyHandler

    Mix-in to support mapping key sequences to methods.

    **Methods**

        .. py:method:: auto_map_keys(pass_info: bool = False,debug: bool = False)

            Set up mappings for methods.

    **Static methods**

        .. py:staticmethod:: mapped(...)

            .. code::

                mapped(
                        mode: str,
                        keyseq: Union[str, Iterable[str]],
                        **kwargs

            Decorator to make a keyboard mapping invoke a method.


            **Parameters**

            .. container:: parameters itemdetails

                *mode*: str
                    The mode in which the mapping applies, one of normal,
                    op-pending, visual or insert.
                *keyseq*: Union
                    A key sequence string or sequence thereof, as used by `map`.
                *kwargs*
                    See `map` for the supported values.

.. rubric:: MapCallback

.. py:class:: MapCallback(*args,**kwargs)

    Wrapper for a function to be invoked by a key mapping.

    This extends the core `Callback` to provide a `MappingInfo` as the first
    positional argument.

    **Parameters**

    .. container:: parameters itemdetails

        *pass_info*
            If True, provide a MappingInfo object as the first argument to
            the callback function.

    **Methods**

        .. py:method:: get_call_args(_vpe_args: Dict[str, Any])

            Get the Python positional and keyword arguments.

            This makes the first positional argument a `MappingInfo` instance,
            unless self.pass_info has been cleared.

.. rubric:: MappingInfo

.. py:class:: MappingInfo(mode: str,keys: str)

    Information passed to a key mapping callback handler.

    The initialisation parameters are made available as attributes.

    **Attributes**

        .. py:attribute:: end_cursor

            When mode=="visual", a tuple (line, column) of the selection
            end. Both values are 1-based. Will be (-1, -1) when not
            applicable.

        .. py:attribute:: keys

            The sequence of keys that triggered the mapping.

        .. py:attribute:: mode

            The mode in which the mapping was triggered (normal, visual,
            op-pending or insert).

        .. py:attribute:: start_cursor

            When mode=="visual", a tuple (line, column) of the selection
            start. Both values are 1-based. Will be (-1, -1) when not
            applicable.

        .. py:attribute:: vmode

            The visual mode (character, line or block). Will be ``None``
            when not applicable.

    **Properties**

        .. py:property:: line_range() -> Optional[Tuple[int, int]]

            The line range, if visual mode was active.

            This is a Python style range.

.. rubric:: imap

.. py:function:: imap(...)

    .. code::

        imap(
                keys: Union[str, Iterable[str]],
                func: Union[Callable, str],
                buffer: bool = True,
                silent: bool = True,
                unique: bool = False,
                pass_info=True,
                nowait: bool = False,
                command: bool = False,
                args=(),
                kwargs: Optional[dict] = None,

    Set up an insert mapping that invokes a Python function.

    See `map` for argument details.

.. rubric:: map

.. py:function:: map(...)

    .. code::

        map(
                mode: str,
                keys: Union[str, Iterable[str]],
                func: Union[Callable, str],
                buffer: bool = True,
                silent: bool = True,
                unique: bool = False,
                nowait: bool = False,
                command: bool = False,
                pass_info=True,
                args=(),
                kwargs: Optional[dict] = None,
                vim_exprs: Tuple[str, ...] = ()

    Set up a key mapping that invokes a Python function.

    By default, the effective map command has the form:

       {m}noremap <buffer> <silent> keys ...

    Where {m} is one of n, x, o, i.

    The noremap form is always used.

    By default the first argument passed to the mapped function is a
    `MappingInfo` object. The *pass_info* argument can be used to prevent this.
    Additional arguments can be specified using *args* and *kwargs*.

    For convenience, mode specific versions are provided (`nmap`, `xmap`,
    `omap` and `imap`). See those for details of what he mapped function can
    do. It is recommended that these mode specific versions are use in
    preference to this function.

    The *func* argument may also be a string, in which case it is interpreted
    as the literal RHS of the key mapping.

    **Parameters**

    .. container:: parameters itemdetails

        *mode*: str
            A string defining the mode in which the mapping occurs. This
            should be one of: normal, visual, op-pending, insert, command,
            select. The command and select mode are not supported when
            *func* is not a string.
        *keys*: Union
            The key sequence to be mapped. This may be an iterable set of
            key sequences that should all be mapped to the same action.
        *func*: Union
            The Python function to invoke for the mapping or a string to
            use as the right hand side of the mapping.
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
        *pass_info*
            If set then the first argument passed to func is a MappingInfo
            object. Defaults to True.
        *args*
            Additional arguments to pass to the mapped function.
        *kwargs*: Optional
            Additional keyword arguments to pass to the mapped function.
        *vim_exprs*: Tuple
            Vim expressions to be evaluated and passed to the callback
            function, when the mapping is triggered.

.. rubric:: nmap

.. py:function:: nmap(...)

    .. code::

        nmap(
                keys: Union[str, Iterable[str]],
                func: Union[Callable, str],
                buffer: bool = True,
                silent: bool = True,
                unique: bool = False,
                pass_info=True,
                nowait: bool = False,
                args=(),
                kwargs: Optional[dict] = None,

    Set up a normal mode  mapping that invokes a Python function.

    See `map` for argument details.

.. rubric:: omap

.. py:function:: omap(...)

    .. code::

        omap(
                keys: Union[str, Iterable[str]],
                func: Union[Callable, str],
                buffer: bool = True,
                silent: bool = True,
                unique: bool = False,
                pass_info=True,
                nowait: bool = False,
                args=(),
                kwargs: Optional[dict] = None,

    Set up an operator-pending mode mapping that invokes a Python function.

    See `map` for argument details.

.. rubric:: xmap

.. py:function:: xmap(...)

    .. code::

        xmap(
                keys: Union[str, Iterable[str]],
                func: Union[Callable, str],
                buffer: bool = True,
                silent: bool = True,
                unique: bool = False,
                pass_info=True,
                nowait: bool = False,
                args=(),
                kwargs: Optional[dict] = None,

    Set up a visual mode mapping that invokes a Python function.

    See `map` for argument details.
