.. _timers:

===========================
Timers and deferred actions
===========================

Vim version 8.0 introduced timers, which invoke a Vim function once or
repeatedly at intervals. VPE provides the `Timer` class to make using Vim's
timers easy and natural in Python code. It also provides a `call_soon` function
that allows actions to be deferred until Vim is able to properly handle them.


The Timer class
---------------

Below is a simple example that performs a ':wall' command every 20 seconds.

.. code-block:: py

    def auto_save(t):
        vpe.commands.wall()

    # Arrange to save all files every 20 seconds. Setting repeat=-1 causes the
    # timer to repeat indefinitely.
    auto_save_timer = Timer(ms=20_000, func=auto_save, repeat=-1)

The `Timer` instance provides a convenient interface for the various timer related
operations.

.. code-block:: py

    # Stop auto saving for a while.
    auto_save_timer.pause()
    assert auto_save_timer.paused
    ...

    # Re-enable auto saving.
    auto_save_timer.resume()
    assert not auto_save_timer.paused

    # Completely stop the timer.
    auto_save_timer.stop()


Timer housekeeping
~~~~~~~~~~~~~~~~~~

VPE performs a small amount of behind-the-scenes housekeeping for some `Timer`
instances. Obviously this housekeeping might not work properly if you mix use
of the `Timer` class with direct invocation of the Vim functions. So you should
generally avoid using ``vim.timer_stop``, *etc.* for timers started using the
`Timer` class.


.. _using_call_soon:

Use of call_soon
----------------

A lot of the time plug-in code may execute when Vim is in a state that does not
allow some actions to be performed. For example, trying to print a message can
silently fail. Vim's timers provide a way to work around such problems.

.. code-block:: py

    # COUNTEREXAMPLE - DO NOT IMITATE

    def check_files_exists(src, dst):
        """Check that the source and destination files actually exist.

        This function may get invoked in a callback.
        """
        def write_err(name):
            vpe.error_msg(f'File {name} does not exist')

        if not os.path.exists(src):
            Timer(0, write_err, args=(src,))
        if not os.path.exists(dst):
            Timer(0, write_err, args=(dst,))

The above code will cause the 'write_err' function to be invoked only once Vim
returns to a suitable state. This means that the messages should be displayed
OK.

This technique can be very useful, but the above code is unwieldy and, for the
above example, the order in which the callbacks are invoked is not defined. So
Vpe provides `call_soon`, which allows the above code in ``check_files_exists``
to simplified as:

.. code-block:: py

    if not os.path.exists(src):
        call_soon(vpe.error_msg, f'File {src} does not exist')
    if not os.path.exists(dst):
        call_soon(vpe.error_msg, f'File {dst} does not exist')

VPE ensures that each each invocation occurs in the order they were passed to
the `call_soon` function.

In fact, the need to generate messages during callback code is common enough
that the `echo_msg`, `warning_msg` and `error_msg` functions provide a ``soon``
keyword argument. So, for the above example, things can be further simplified.

.. code-block:: py

    if not os.path.exists(src):
        vpe.error_msg(f'File {src} does not exist', soon=True)
    if not os.path.exists(dst):
        vpe.error_msg(f'File {dst} does not exist', soon=True)
