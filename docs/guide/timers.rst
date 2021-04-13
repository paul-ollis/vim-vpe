===========================
Timers and deferred actions
===========================

Vim version 8.0 introduced timers, which invoke a Vim function once or
repeatedly at intervals. VPE provides the `Timer` class to make using Vim's
timers easy and natural in Python code. It also provides a `call_soon` function
that makes use o zero length timer to help make things occur in the correct
order.


The Timer class
---------------

Below is a simple example that performs a 'wall' command every 20 seconds.

.. code-block:: py

    def auto_save(t):
        vpe.commands.wall()

    # Arrange to save all files every 20 seconds. Setting repeat-1 causes the
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
------------------

VPE performs a small amount of behind-the-scenes housekeeping for some `Timer`
instance. Obviously this housekeeping might not work properly if you mix use of
the `Timer` class with direct invocation of the Vim functions.

.. code-block:: py

    def connection_timeout(t):
        """Handle failure of a connection attempt."""
        ...

    def handle_connection_ok():
        """Cancel connection failure timeout."""
        # This is a bad idea, use conn_timeout_timer.stop().
        vim.timer_stop(conn_timeout_timer.id)

    conn_timeout_timer = Timer(ms=5_000, func=connection_timeout)
    ...

Vim provides a :vim:`timer_stopall()` as a kind of emergency stop. If you use
`vpe.timer_stopall` in preference then VPE's timer housekeeping will also be
performed.


Use of call_soon
----------------

A lot of of the time plug-in code is actually executing Vim is in a state when
some actions cannot be performed. For example, trying to print a message can
silently fail. Vim's timers provide a way to work around such problems.

.. code-block:: py

    def check_curfile_exists():
        """Check that the current buffer's file actually exists.

        This may get invoked in a callback function.
        """
        if not os.path.exists(vim.current.buffer.name):

            def write_err():
                vpe.error_msg(f'File {current.buffer.name} does not exist')

            Timer(0, write_err)

The above code will cause the 'write_err' function to be invoked as soon as Vim
returns to a state when it is waiting for user input. At his point, the message can be
displayed OK.

This technique can be very useful, but the above code is unwieldy so Vpe
provides `call_soon`, which allows the above code in ``check_curfile_exists``
to simplified as:

.. code-block:: py

    if not os.path.exists(vim.current.buffer.name):
        call_soon(vpe.error_msg, f'File {current.buffer.name} does not exist')
