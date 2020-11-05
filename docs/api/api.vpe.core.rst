Module vpe.core
===============

.. py:module:: vpe.core

Enhanced module for using Python3 in Vim.

This provides the Vim class, which is a wrapper around Vim's built-in *vim*
module. It is intended that a Vim instance can be uses as a replacement for the
*vim* module. For example:

.. code-block:: py

    from vpe import vim
    # Now use 'vim' as an extended version of the *vim* module.
    # ...

Callback
--------

.. py:class:: vpe.core.Callback(...)

    .. parsed-literal::

        Callback(
            func,
            \*,
            py_args=(),
            py_kwargs={},
            vim_exprs=(),
            pass_bytes=False,
            \*\*kwargs)

    Wrapper for a function to be called from Vim.

    This encapsulates the mechanism used to arrange for a Python function to
    be invoked in response to an event in the 'Vim World'. A Callback stores
    the Python function together with an ID that is uniquely associated with
    the function (the UID). If, for example this wraps function 'spam' giving
    it UID=42 then the Vim script code:

    ::

        :call VPE_Call(42, 'hello', 123)

    will result in the Python function 'spam' being invoked as:

    .. code-block:: py

        spam('hello', 123)

    The way this works is that the VPE_Call function first stores the UID
    and arguments in the global Vim variable _vpe_args_ in a dictionary
    as:

    .. code-block:: py

        {
            'uid': 42,
            'args': ['hello', 123]
        }

    Then it calls this class's `invoke` method:

    ::

        return py3eval('vpe.Callback.invoke()')

    The `invoke` class method extracts the UID and uses it to find the
    Callback instance.

    **Parameters**

    .. container:: parameters itemdetails

        *func*
            The Python function to be called back.
        *py_args*
            Addition positional arguments to be passed to *func*.
        *py_kwargs*
            Additional keyword arguments to be passed to *func*.
        *vim_exprs*
            Expressions used as positional arguments for the VPE_Call
            helper function.
        *pass_bytes*
            If true then vim byte-strings will not be decoded to Python
            strings.
        *kwargs*
            Additional info to store with the callback. This is used
            by subclasses - see 'MapCallback' for an example.

    **Methods**

        .. py:method:: vpe.core.Callback.as_call()

            Format a command of the form 'call VPE_xxx(...)'

            The result can be used as a colon prompt command.

        .. py:method:: vpe.core.Callback.as_invocation()

            Format a command of the form 'VPE_xxx(...)'

            The result is a valid Vim script expression.

        .. py:method:: vpe.core.Callback.as_vim_function()

            Create a vim.Function that will route to this callback.

        .. py:method:: vpe.core.Callback.format_call_fail_message()

            Generate a message to give details of a failed callback invocation.

            This is used when the `Callback` instance exists, but the call raised
            an exception.

        .. py:method:: vpe.core.Callback.get_call_args(_vpe_args: Dict[str, typing.Any])

            Get the Python positional and keyword arguments.

            This may be over-ridden by subclasses.

    **Class methods**

        .. py:classmethod:: vpe.core.Callback.invoke()

            Invoke a particular callback function instance.

            This is invoked from the "Vim World" by VPE_Call. The global Vim
            dictionary variable _vpe_args_ will have been set up to contain 'uid'
            and 'args' entries. The 'uid' is used to find the actual `Callback`
            instance and the 'args' is a sequence of Vim values, which are passed
            to the callback as positional areguments.

        .. py:classmethod:: vpe.core.Callback.on_del(uid)

            "Handle deletion of weak reference to method's instance.

expr_arg
--------

.. py:class:: vpe.core.expr_arg(arg: str)

    Wrapper for a Vim argument that is an expression.

    This is used to wrap a string that represents an expression that should be
    passed to a Vim function, without being quoted.

    **Parameters**

    .. container:: parameters itemdetails

        *arg*
            The argument as a string representing the Vim expression.