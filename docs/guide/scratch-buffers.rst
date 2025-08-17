===============
Scratch buffers
===============

.. |init_options| replace:: `init_options<ScratchBuffer.init_options>`
.. |modifiable| replace:: `modifiable<ScratchBuffer.modifiable>`
.. |on_first_showing| replace:: `on_first_showing<ScratchBuffer.on_first_showing>`
.. |set_ext_name| replace:: `set_ext_name<ScratchBuffer.set_ext_name>`
.. |show| replace:: `show<ScratchBuffer.show>`

Many Vim plug-ins need to display information in a buffer that is not user
editable and does not get saved to a file; often referred to as a scratch
buffer. The `ScratchBuffer` class, which is a specialisation of the `Buffer`
class, provides a convenient way to manage such buffers.


ScratchBuffer creation
======================

It is recommended that you use the `get_display_buffer` function rather than
create `ScratchBuffer` instances directly. This function takes care of:

- creating a new Vim buffer if necessary.
- choosing a suitable name for the buffer (one that is a very unlikely file
  name).
- actually creating the `ScratchBuffer` instance, if it does not already exist.

The `get_display_buffer` function takes a name, which identifies the scratch
buffer. The same `ScratchBuffer` instance is returned each time
`get_display_buffer` is called with the same name.

.. code-block:: py

    # Create a display (scratch) buffer, uniquely defined by the name 'info'.
    # The buffer's (initial) name will be '/[[info]]'.
    disp_buf = vpe.get_display_buffer('info')
    ....
    scratch_buf = vpe.get_display_buffer('info')
    scratch_buf is disp_buf   # True.


Displaying and updating
=======================

The |show| method allows the buffer to be made visible either within the
current window or after first splitting the current window. Calling *show()*
without arguments, simply switches to the scratch buffer. To open in a split
use either the *splitlines* or *splitcols* argument. The scratch buffer is
shown in the upper or left part of the split.

The way the *splitlines* and *splitcols* arguments work are shown below. ::

         splitlines = -3                           splitlines = 3
    .-----------------------.                 .-----------------------.
    |                       |                 |                       |
    |     ScratchBuffer     |                 |     ScratchBuffer     |
    |                       |                 |                       |
    |-----------------------|                 :                       :
    |                       |                 |                       |
    |                       |                 |                       |
    |                       |                 |                       |
    :                       :                 |-----------------------|
    |                       |                 |                       |
    |                       |                 |                       |
    |                       |                 |                       |
    `-----------------------'                 `-----------------------'

         splitcols = -3                             splitcols = 3
    .-----------------------.                 .-----------------------.
    | S |                   |                 |          S        |   |
    | c |                   |                 |          c        |   |
    | r |                   |                 |          r        |   |
    | a |                   |                 |          a        |   |
    | t |                   |                 |          t        |   |
    | c |                   |                 |          c        |   |
    | h |                   |                 |          h        |   |
    | B |                   |                 |          B        |   |
    | u |                   |                 |          u        |   |
    | f |                   |                 |          f        |   |
    | f |                   |                 |          f        |   |
    | e |                   |                 |          e        |   |
    | r |                   |                 |          r        |   |
    `-----------------------'                 `-----------------------'

The |show| method tries to take care not to change the size of other windows as
shown below. ::

    .--------------------.                          .--------------------.
    |                    |                          |                    |
    |                    |                          |   ScratchBuffer    |
    |     Buffer  A      |   show(splitlines=-3)    |                    |
    |                    | -----------------------> |--------------------|
    |                    |                          |    Buffer  A       |
    |--------------------|                          |--------------------|
    |                    |                          |                    |
    |                    |                          |                    |
    |     Buffer  B      |                          |    Buffer  B       |
    |                    |                          |                    |
    |                    |                          |                    |
    |                    |                          |                    |
    `--------------------'                          `--------------------'

A `ScratchBuffer` has its attributes set to prevent direct user modification of
the contents. The |modifiable| method provides a context manager that makes it
easy to update the buffer contents programmatically. For example to add a line,
just do:

.. code-block:: py

    with disp_buf.modifiable():
        disp.buf.append('A added line')


Managing the buffer
===================

Buffer name
-----------

The name given to a `ScratchBuffer` is composed of two parts, derived from the
name passed to `get_display_buffer` and an extension name. The extension name is
initially empty, but can me changed by |set_ext_name|.

.. code-block:: py

    # Create buffer to display Man pages. It will initially be called
    # /[[manpage]].
    man_buf = vpe.get_display_buffer('manpage')
    ...

    # Set the extended name, in preparation for displaying Vim's man page. The
    # buffer's name will now be /[[manpage]]/vim.
    man_buf.set_ext_name('vim')
    ...


Special identifiers
-------------------

A `ScratchBuffer` provides properties that are useful prefixes when defining
syntax, auto-commands, *etc.* specific to the buffer.

.. code-block:: py

    # Add syntax highlighting for the Man page.
    with syntax.Syntax(man.syntax_prefix) as syn:
        ...

    # Create buffer specific auto-commands.
    with vpe.AutoCmdGroup(man.auto_grp_name) as au:
        au.delete_all()
        ...

.. _subclassing_scratchbuffer:

Subclassing ScratchBuffer
=========================

The `ScratchBuffer` classed may be sub-classed to meet your plug-in's needs.
You should still use `get_display_buffer` for creation. Just pass your subclass
as the *buf_class* argument.

A couple of the `ScratchBuffer` methods are specifically intended to be
extended by subclasses - |init_options| and |on_first_showing|. The
|init_options| method is the place to set any special buffer specific option
values. The |on_first_showing| method is invoked once, the first time the
buffer becomes visible in a window. This is useful for performing any
initialisation that depends on the buffer being current, such as defining syntax
highlighting.

.. code-block:: py

    class ManPageBuffer(vpe.ScratchBuffer):
        """A buffer tuned to displaying man pages."""

        def on_first_showing(self):
            # Add syntax highlighting for the Man page.
            with syntax.Syntax(self.syntax_prefix) as syn:
                ...

    man_buf = vpe.get_display_buffer('manpage', buf_class=ManPageBuffer)
