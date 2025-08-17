=============
Using Windows
=============

.. |close()| replace:: :py:obj:`close<Window.close>`
.. |goto()| replace:: :py:obj:`goto<Window.goto>`
.. |id| replace:: :py:obj:`id<Window.id>`
.. |temp_options()| replace:: :py:obj:`temp_options<Window.temp_options>`
.. |visible_line_range()| replace:: :py:obj:`visible_line_range<vpe.Window.visible_line_range>`


Basics
------

VPE provides a `Window` as a wrapper around Vim's built in window class. All
VPE objects return a `Window` instead of a plain old Vim window.

A given `Window` becomes unusable if the underlying Vim window is closed, so
check that *valid* is ``True`` if there is any doubt. In practice, most code is
able to assume that the *valid* property is set.


Attributes and methods
----------------------

The `Window` class provides all the attributes and methods of Vim's window
class. However some attribute types and return values are different. In such
cases, the VPE value is compatible with the Vim type. The differences are listed
in the following table.

    ====================  =================  =================
    Attrribute            Vim type           VPE type
    --------------------  -----------------  -----------------
    vars                  vim.dictionary     `Variables`
    options               vim.options        `Options`
    tabpage               vim.tabpage        `TabPage`
    buffer                vim.buffer         `Buffer`
    ====================  =================  =================

The `Window` class also provides a number of additional properties and methods, including:

.. hlist::
    :columns: 3

    - |close()|
    - |goto()|
    - |id|
    - |temp_options()|
    - |visible_line_range()|

The |temp_options()| context manager provides exactly the same function for a
`Window` s does the `Buffer.temp_options` method. Read :ref:`temporary buffer
options<temp_buf_options>` to see how this is used.

The |id| is the unique window ID (not its number) that is required as the
argument for a number of built-in Vim functions; such as :vim:`getwininfo()`.


Context Managers
----------------

The `vpe` module provides some context managers that support working with
windows.

The `saved_current_window` context manager is useful when executing code that
might switch to another window.

.. code-block:: py

    with vpe.saved_current_window():
        ...
        # May change current window, but that change will be undone when the
        # context exits.
        split_window_if_required()

If you need to temporarily switch to a different window, use
`temp_active_window`.

.. code-block:: py

    with vpe.temp_active_window(alt_window):
        # Now vim.current.window will be alt_window for the duration of the
        # context.
        ...

Vim provides the functions :vim:`winsaveview()` and :vim:`winrestview()` as a
mechanism to 'protect' the user from operations that jump around a buffer. The
`saved_winview` context manager wraps these up more conveniently.

.. code-block:: py

    with vpe.saved_winview():
        vim.command('$')
        ...
