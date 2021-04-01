=============
Using Buffers
=============

.. |bufnr| replace:: `bufnr<Buffer.bufnr>`
.. |changed| replace:: `changed<Buffer.changed>`
.. |changedtick| replace:: `changedtick<Buffer.changedtick>`
.. |find_active_windows()| replace:: `find_active_windows()<Buffer.find_active_windows>`
.. |find_best_active_window()| replace:: `find_best_active_window()<Buffer.find_best_active_window>`
.. |goto_active_window()| replace:: `goto_active_window()<Buffer.goto_active_window>`
.. |is_active()| replace:: `is_active()<Buffer.is_active>`
.. |lastused| replace:: `lastused<Buffer.lastused>`
.. |linecount| replace:: `linecount<Buffer.linecount>`
.. |list()| replace:: `list()<Buffer.list>`
.. |lnum| replace:: `lnum<Buffer.lnum>`
.. |loaded| replace:: `loaded<Buffer.loaded>`
.. |location| replace:: `location<Buffer.location>`
.. |long_display_name| replace:: `long_display_name<Buffer.long_display_name>`
.. |popups| replace:: `popups<Buffer.popups>`
.. |short_display_name| replace:: `short_display_name<Buffer.short_display_name>`
.. |store()| replace:: `store<Buffer.store>`
.. |temp_options()| replace:: `temp_options()<Buffer.temp_options>`
.. |type| replace:: `type<Buffer.type>`


Always the same instance
------------------------

VPE provides a `Buffer` as a wrapper around Vim's built in buffer class. All VPE
objects return a `Buffer` instead of a plain old Vim buffer. VPE also makes sure
that you always get the same `Buffer` object for a given Vim buffer.

.. code-block:: py

    from vpe import vim

    a_buffer = vim.buffers[0]
    isinstance(a_buffer, vpe.Buffer)     # True

    another_buffer = vim.buffers[0]
    a_buffer is another_buffer           # True

    if vim.current.window.buffer is a_buffer:
        # The 'a_buffer' is currently active.
        ...


Attributes and methods
----------------------

The `Buffer` class provides all the attributes and methods of Vim's buffer
class. However some attribute types and return values are different. In such
cases, the VPE value is compatible with the Vim type. The differences are listed
in the folling table.

    ====================  =================  =================
    Attrribute or method  Vim type           VPE type
    --------------------  -----------------  -----------------
    vars                  vim.dictionary     `Variables`
    options               vim.options        `Options`
    range()               vim.range          `Range`
    ====================  =================  =================

The `Buffer` class also provides a number of additional properties and methods, including:

.. hlist::
    :columns: 3

    - |bufnr|
    - |changed|
    - |changedtick|
    - |find_active_windows()|
    - |find_best_active_window()|
    - |goto_active_window()|
    - |is_active()|
    - |lastused|
    - |linecount|
    - |list()|
    - |lnum|
    - |loaded|
    - |location|
    - |long_display_name|
    - |popups|
    - |short_display_name|
    - |store()|
    - |temp_options()|
    - |type|

Some of these are discussed in more detail below.


Modifying contents
------------------

As well as supporting all the standard :vim:`python-buffer` ways of modifying
buffer's contents, VPE also provides the |list()| context manager method. The way
this is used is:

.. code-block:: py

    with buf.list() as lines:
        # The 'lines' variable is a sequence containing a copy of all the lines
        # in the buffer. Manipulate lines as required. The lines sequence will
        # replace the buffer contents when the context exits.
        list[10:] = last_few_lines
        ...

The above code is roughly equivalent to:

.. code-block:: py

    lines = buf[:]
    try:
        list[10:] = last_few_lines
        ...
    finally:
        buf[:] = lines

Although, on the face of it, this seems an inefficient way to modify a buffer,
it can actually be much faster for non-trivial changes to a buffers contents.
Manipulation of Python lists is very efficient and many 'context switches'
between Python and Vim can be avoided.


Buffer store
------------

Vim provides buffer variables (:vim:`buffer-variable`) as a mechanism to
associate arbitrary information with a given buffer. These are available
using the `Buffer.vars` property, but VPE provides an alternative that can
be more convenient: the |store()|. Each entry in the buffer's store is a
`Struct` and is accessed by name.

.. code-block:: py

    info = buf.store('info')          # Entry is created is it does not exist.
    info.author = 'Paul'              # Add or modify any arbitrary attributes.
    info.last_modified = time.time()
    ...

One major advantage over buffer variables is the ability easily associate any
type of Python value with a buffer.


.. _temp_buf_options:

Temp options
------------

There are occisions when you need to temporarily modify one or more of a
buffer's options. A common example is to allow programmatic modification of a
read-only buffer's contents. One approach is:

.. code-block:: py

    # Save option values.
    saved = buf.options.readonly, buf.options.modifiable

    buf.options.readonly = False
    buf.options.modifiable = True
    try:
        # Make the changes to the buffer.
        ...
    finally:
        buf.options.readonly, buf.options.modifiable = saved

The |temp_options()| context manager makes this simpler, slicker, more flexible
and less error prone. The above can simplified to:

.. code-block:: py

    with buf.temp_options(readonly=False, modifiable=True):
        # Make the changes to the buffer.
        ...

You can also modify options within the context, which will be restored when the
context ends.

.. code-block:: py

    # Update the buffer, without setting the modified flag.
    with buf.temp_options(readonly=False, modifiable=True) as options:
        # Make the changes to the buffer.
        ...

        # Prevent the above changes from making the buffer appear modified.
        options.modified = False

In the above example, if :vim:`'modified'` was set before the temp_options context then
it will still be set after.
