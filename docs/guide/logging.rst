The VPE and other logs
======================

If you do any non-trivial Python scripting within Vim, it is very likely that
you will find it helpful to be able to write log message. Python programmers
often simply use calls to ``print()`` for this and this can be useful from
within Vim. However, such output will typically cause the Vim window to scroll
and wait for the user to press a key. This can be inconvenient during Python
scripting development.

A simple way to work around this is to open a file and write to that instead.
The log file can be loaded into to Vim and, perhaps, its :vim:`'autoread'`
option be set.

VPE provides an additional way to support scripting logging. The `vpe.log`
object.


The vpe.log
-----------

This acts as a simple alternative to the ``print()`` function that directs its
output to a Vim buffer.

.. code-block:: python

    from vpe import log

    log('This will go to the VPE log buffer.')

The easiest way to make the VPE log buffer visible is to use `Log.show`.

.. code-block:: python

    # Make the log buffer visible in a split window.
    log.show()

The log buffer has some special behaviours.

- The text in the log buffer is shown with a simple time stamp of seconds and
  hundredths of a second.

- The number of lines in the buffer is limited. When the limit is reached,
  older lines are deleted. The default length is 500 lines, but this can be
  changed using the `Log.set_maxlen` method.

- When the log buffer is being shown in a window, it is automatically scrolled
  to show new output as it gets written.

You can also redirect ``sys.stdout`` and ``sys.stderr`` to the VPE log.

.. code-block:: python

    # Make all future printing go to the VPE log. This also redirects
    # sys.stderr.
    log.redirect()

    ...

    # Undo effect of the last call to redirect.
    log.unredirect()

I personally find it convenient to always have redirection enabled, which I do
in my personal Vim initialisation scripts. I also have a key mapping to make it
easy to quickly view the log.

.. code-block:: vim

    :nmap <S-F1> :py3 vpe.log.show()<cr>


Error logging
~~~~~~~~~~~~~

When VPE traps an error condition, it will normally write one or more error
messages to the `vpe.log`. This is typically less disruptive that writing to
the Vim console.

Currently the log output does not distinguish between normal output and errors.
This may well change in the future.


Other logs
----------

The `vpe.log` object is actually just a specific instance of the `vpe.Log`
class. VPE only creates the `vpe.log` automatically, but it can be more useful
to create your own `Log` for your script or plug-in. This keeps your plug-in's
log output nicely separate.
