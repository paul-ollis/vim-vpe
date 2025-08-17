Mapping key sequences
---------------------

.. |end_cursor| replace:: :ref:`end_cursor<info_attrs>`
.. |imap| replace:: :py:obj:`imap<vpe.mapping.imap>`
.. |MappingInfo| replace:: :py:obj:`MappingInfo<vpe.mapping.MappingInfo>`
.. |map| replace:: :py:obj:`map<vpe.mapping.nmap>`
.. |nmap| replace:: :py:obj:`nmap<vpe.mapping.nmap>`
.. |omap| replace:: :py:obj:`omap<vpe.mapping.omap>`
.. |start_cursor| replace:: :ref:`start_cursor<info_attrs>`
.. |vmode| replace:: :ref:`vmode<info_attrs>`
.. |xmap| replace:: :py:obj:`xmap<mapping.xmap>`


VPE provides the following mode specific functions that can be used to defined
key mappings.

.. hlist::
    :columns: 4

    - |imap|
    - |nmap|
    - |omap|
    - |xmap|

These roughly correspond to the vim commands of the same name. Vim's other
mapping commands are not supported because I have not come across any good
reasons to use them within Python based scripts.

Apart from creating mappings for different Vim modes, there is little
difference between them. So most of the following discussion uses |nmap|.

Key mappings are typically set up to invoke Python functions or methods.

.. code-block:: python

    from vpe import mapping

    def on_key(info: mapping.MappingInfo):
        vpe.echo_msg(f'Key sequence {info.keys} was pressed', soon=True)

    mapping.nmap(keys='g<F1>', func=on_key)

.. sidebar:: Argument soon=True

    Notice that the call to vpe.echo_msg uses the argument ``soon=True``. See
    :ref:`using_call_soon` to find out why.

After the above is executed, a mapping will be set up for the *current* buffer
such that the key sequence 'g', '<F1>' (in normal mode) will cause the message
'Key sequence g<F1> was pressed' to be displayed. Notice that the callback
function ``on_key`` receives a |MappingInfo| object. This provides details
about how and why the callback was invoked. This makes it easy to handle
multiply key mappings in multiple modes, using just one function; which can
simplify code in some circumstances. The information contained in the
|MappingInfo| object is:

.. _info_attrs:

mode
    The mode in which the mapping was triggered (normal, visual, op-pending or
    insert).
keys
    The sequence of keys that triggered the mapping.
vmode
    The visual mode (character, line or block). Will be ``None`` when not
    applicable.
start_cursor
    When mode=="visual", a tuple (line, column) of the selection start. Both
    values are 1-based. Will be (-1, -1) when not applicable.
end_cursor
    When mode=="visual", a tuple (line, column) of the selection end. Both
    values are 1-based. Will be (-1, -1) when not applicable.


Defaults and limitations
~~~~~~~~~~~~~~~~~~~~~~~~

The mapping functions impose some limitations and non-obvious defaults. The
actual mapping command generated for the above example helps illustrate this:

.. code-block:: vim

    :nnoremap <special> <buffer> <silent> g<F1>
        \ :silent call VPE_Call("154", "on_key")<CR>

The other mapping functions produce broadly similar code; i.e. they typically
invoke ``VPE_Call``.

- The 'nnoremap' command is used. VPE always uses the noremap form to set up
  key mappings. No support for nested/recursive mapping is provided. I have not
  found this restriction to be a problem.

- The <special> option is always used. This helps avoid surprises.

- The <buffer> and <silent> options are used by default. These are chosen as
  suitable defaults for most scripting (admittedly based on my experience). These
  can be over-ridden using the buffer and silent keyword arguments:

  .. code-block:: python

      mapping.nmap(keys='g<F1>', func=on_key, buffer=False, silent=False)

- The <script> and <expr> options are not supported. This may change
  if compelling use cases come to light (please add an issue if you have such a
  use case, at https://github.com/paul-ollis/vim-vpe/issues).


What is VPE_Call("154", "on_key")
'''''''''''''''''''''''''''''''''

The above nnoremap command includes the Vim code ``VPE_Call("154", "on_key")``.
You do not need to care much about this, but some background information is
useful. The mapping, as displayed by the Vim command ``:nmap g<F1>``, is also
illustrative.::

    n  g<F1>       *@:silent call VPE_Call("154", "on_key")<CR>

The VPE_Call function is the first stage in routing the key mapping to the
correct Python function. The first argument is a unique, internally generated,
code that VPE uses to lookup up the correct Python function or method. The
second argument is not used by VPE, it is added just so that the output of
``:nmap g<F1>`` gives a hint to the user or plug-in developer about the
Python function that will be invoked.


Mapping options
~~~~~~~~~~~~~~~

The |nmap|, *etc.* functions support a number of additional keyword argument
options.

The |MappingInfo| argument can be suppressed. Can be preferable if the callback function
only handles one key sequence and mode.

.. code-block:: python

    def on_key():
        vpe.echo_msg(f'Key sequence g<F1> was pressed', soon=True)

    mapping.nmap(keys='g<F1>', func=on_key, pass_info=False)

The <nowait> and <unique> mapping options can be used.

.. code-block:: python

    mapping.nmap(keys='g<F1>', func=on_key, nowait=True, unique=True)

Additional positional and keyword arguments can be passed to the callback
function.

.. code-block:: python

    from vpe import mapping

    def on_key(_info, key, mode):
        vpe.echo_msg(f'Key sequence {key} was pressed in {mode} mode', soon=True)

    mapping.nmap(
        keys='g<F1>',
        func=on_key,
        args=('g<F1>',),
        kwargs={'mode': 'normal'})


Other modes
~~~~~~~~~~~

The |xmap| function, creates a mapping for the visual mode. The mapping command
generated is of the form:

.. code-block:: vim

    :xnoremap <special> <buffer> <silent> g<F1>
        \ :<C-U>silent call VPE_Call("154", "on_key")<CR>

The ``<C-U>`` clears the leading ``'<,'>`` that Vim inserts on the command
line. The |MappingInfo| object passed to the callback has the |vmode|,
|start_cursor| and |end_cursor| attributes set to meaningful values.

The |omap| function, creates a mapping for the operator pending mode. The
mapping command generated is of the form:

.. code-block:: vim

    :onoremap <special> <buffer> <silent> g<F1>
        \ :<C-U>silent call VPE_Call("154", "on_key")<CR>

As for |xmap| the ``<C-U>`` clears any position argument that Vim inserts on
the command line.

The |imap| function creates  a mapping for the insert mode. The mapping command
generated is in one of two forms:

.. code-block:: vim

    :inoremap <special> <buffer> <silent> g<F1>
        \ <C-R>=:VPE_Call("154", "on_key")<CR>

    :inoremap <special> <buffer> <silent> g<F1>
        \ <C-\><C-N>:silent call VPE_Call("154", "on_key")<CR>

The first form is generated by default. In this case the callback should return
a string, which will be inserted into the buffer.

The second form is generated if ``command=True`` is passed to |imap| (only imap
uses the ``command`` argument). In this case, the value returned from the
callback is not used.


The map function
~~~~~~~~~~~~~~~~

The mapping module also includes a |map| function. The functions |nmap|,
|omap|, *etc.* are all thin wrappers around this more generic function. This
takes an additional, initial argument ``mode``, which must be one of the
strings 'normal', 'visual', 'op-pending' or 'insert'.

The |map| function can be more convenient when, for example, creating mappings
based on some form of user configuration.


Plain old mappings
~~~~~~~~~~~~~~~~~~

It is permitted to pass a string as the ``func`` argument to |map|, |nmap|,
*etc*. If you do then the argument is just the right hand side of the generated
mapping. For example, the following:

.. code-block:: python

    from vpe import mapping

    mapping.nmap('g<F1>', ':echo "Pressed g<F1>"<CR>')

is equivalent to the Vim command:

.. code-block:: vim

    nmap <special> <buffer> <silent> g<F1> :echo "Pressed g<F1>"<CR>

This example avoids using the keyword argument form for the |nmap| keys and
func arguments. I think this is less confusing than:

.. code-block:: python

    mapping.nmap(keys='g<F1>', func=':echo "Pressed g<F1>"<CR>')


Using decorators
~~~~~~~~~~~~~~~~

.. note::

    This feature should be considered experimental at the moment. It will not
    be removed, but detailed behaviour, argument names, *etc.* may change in
    the next release.

For classes, VPE provides decorator based mechanism for mapping key sequences
to methods. This is most easily described using example code:

.. code-block:: python

    from vpe import mapping


    class MyPlugin(mapping.KeyHandler):

        def __init__(self):
            # Initialise MyPlugin.
            self.auto_map_keys()

        @mapping.KeyHandler.mapped(mode='normal', keyseq='g<F1>')
        def on_key(self):
            vpe.echo_msg(f'Key sequence g<F1> was pressed', soon=True)

        @mapping.KeyHandler.mapped(mode='normal', keyseq='g<C-F1>')
        def on_other_key(self):
            vpe.echo_msg(f'Key sequence g<C-F1> was pressed', soon=True)


    plugin = MyPlugin()

This can make code easier to read and maintain in some circumstances,
but it is not as flexible as |nmap| *etc*.

Note that the mappings are only created when the ``self.auto_map_keys()``
method is invoked.  Also note that, by default, the methods do not receive a
|MappingInfo| object as the first argument. Give the ``mapped`` decorator a
``pass_info=True`` argument to change this behaviour. Finally note that
the mapping mode must be provided. In my code I typically use ``functools.partial``
to create a class local decorator, for example:

.. code-block:: python

    from functools import partial

    from vpe import mapping


    class MyPlugin(mapping.KeyHandler):

        nmap = partial(mapping.KeyHandler.mapped, mode='normal')

        def __init__(self):
            # Initialise MyPlugin.
            self.auto_map_keys()

        @nmap('g<F1>')
        def on_key(self):
            vpe.echo_msg(f'Key sequence g<F1> was pressed', soon=True)

        @nmap('g<C-F1>')
        def on_other_key(self):
            vpe.echo_msg(f'Key sequence g<C-F1> was pressed', soon=True)
