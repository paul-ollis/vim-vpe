Module vpe.core
===============


.. py:module:: core

Enhanced module for using Python 3 in Vim.

This provides the Vim class, which is a wrapper around Vim's built-in *vim*
module. It is intended that a Vim instance can be uses as a replacement for the
*vim* module. For example:

.. code-block:: py

    from vpe import vim
    # Now use 'vim' as an extended version of the ``vim`` module.
    # ...

.. rubric:: expr_arg

.. py:class:: expr_arg(arg: str)

    Wrapper for a Vim argument that is an expression.

    This is used to wrap a string that represents an expression that should be
    passed to a Vim function, without being quoted.

    **Parameters**

    .. container:: parameters itemdetails

        *arg*
            The argument as a string representing the Vim expression.
