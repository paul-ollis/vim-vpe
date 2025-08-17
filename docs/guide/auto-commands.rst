===========================
Events, *aka* auto-commands
===========================

.. |add| replace:: `vpe.AutoCmdGroup.add`
.. |AutoCmdGroup| replace:: `vpe.AutoCmdGroup`
.. |Buffer| replace:: `vpe.Buffer`
.. |ScratchBuffer| replace:: `vpe.ScratchBuffer`
.. |BufEventHandler| replace:: `vpe.BufEventHandler`


Defining commands
=================

In plug-in code it is common to place all auto-commands into one or more groups,
leading to code like:

.. code-block:: vim

    augroup MyGroup
      autocmd!
      autocmd BufEnter <buffer=8> call s:RefreshContent()
      autocmd BufLeave <buffer=8> call s:SaveChanges()
    augroup END

VPE provides the class |AutoCmdGroup|, which is a context manager that
supports the same sort of pattern. The equivalent of the above Vim code
would be something like:

.. code-block:: python

    import vpe
    from vpe import vim

    b = vim.current.buffer
    with vpe.AutoCmdGroup('MyGroup') as g:
        g.delete_all()
        g.add('BufEnter', refresh_content, pat=b)
        g.add('BufLeave', save_changes, pat=b)

The correspondence with the Vim script should be fairly clear. The ``pat``
argument act in a similar way to the ``{pat}}`` of the :vim:`:autocmd`.
It can be omitted if you want the event only to be handled for the current
buffer (so it is not actually necessary in the above example). If you set it
to a |Buffer| instance then the handler is installed for just that buffer.
Or you can pass a string, which is treated in the same way as :vim:`:autocmd`.

The |add| takes two boolean keyword only arguments ``once`` and ``nested``,
which correspond to the corresponding :vim:`:autocmd` options
:vim:`:autocmd-once` and :vim:`:autocmd-nested`. Any other keyword arguments
are passed a keyword arguments to the handling function.


Using decorators
================

.. note::

    This feature should be considered experimental at the moment. It will not
    be removed, but detailed behaviour, argument names, *etc.* may change in
    the next release.

As for key mapping and user defined commands, VPE provides a decorator approach
to handling events. Here is another way to implement the previous examples.

.. code-block:: python

    import vpe
    from vpe import vim


    class MyPlugin(vpe.EventHandler):
        handle = vpe.EventHandler.handle

        def __init__(self):
            b = vim.current.buffer
            self.auto_define_event_handlers('MyGroup', delete_all=True)

        @handle('BufEnter', pat='<buffer>')
        def refresh_content(self):
            ...

        @handle('BufLeave', pat='<buffer>')
        def save_changes(self):
            ...

It is quite common to use this approach in specialisations of the
|ScratchBuffer|, in which case event handling methods should be specific to the
scratch buffer. VPE provides the |BufEventHandler| mixin class for this specific
case, resulting in code like:

.. code-block:: python

    import vpe
    from vpe import vim


    class MyWorkBuffer(vpe.ScratchBuffer, vpe.BufEventHandler):
        handle = vpe.BufEventHandler.handle

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.auto_define_event_handlers('MyGroup', delete_all=True)

        @handle('BufEnter')
        def refresh_content(self):
            vpe.echo_msg('Enter', soon=True)

        @handle('BufLeave')
        def save_changes(self):
            vpe.echo_msg('Leave', soon=True)


    s = vpe.get_display_buffer(name='DisplayBuf', buf_class=MyWorkBuffer)

Notice that the ``pat`` argument is not used.

See :ref:`subclassing_scratchbuffer` for more information on subclassing
the |ScratchBuffer| class.
