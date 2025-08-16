========
Channels
========

.. _subprocess: https://docs.python.org/3/library/subprocess.html

.. |callback| replace:: :vim:`channel-callback`
.. |call_soon| replace:: vpe.call_soon`
.. |Channel| replace:: `channels.Channel`
.. |channels| replace:: :py:obj:`wrappers.channels`
.. |ch_canread| replace:: :vim:`ch_canread()`
.. |ch_close_in| replace:: :vim:`ch_close_in()`
.. |ch_close| replace:: :vim:`ch_close()`
.. |ch_evalexpr| replace:: :vim:`ch_evalexpr()`
.. |ch_evalraw| replace:: :vim:`ch_evalraw()`
.. |ch_getbufnr| replace:: :vim:`ch_getbufnr()`
.. |ch_getjob| replace:: :vim:`ch_getjob()`
.. |ch_info| replace:: :vim:`ch_info()`
.. |ch_logfile| replace:: :vim:`ch_logfile()`
.. |ch_log| replace:: :vim:`ch_log()`
.. |ch_open| replace:: :vim:`ch_open()`
.. |ch_readblob| replace:: :vim:`ch_readblob()`
.. |ch_readraw| replace:: :vim:`ch_readraw()`
.. |ch_read| replace:: :vim:`ch_read()`
.. |ch_sendexpr| replace:: :vim:`ch_sendexpr()`
.. |ch_sendraw| replace:: :vim:`ch_sendraw()`
.. |ch_setoptions| replace:: :vim:`ch_setoptions()`
.. |ch_status| replace:: :vim:`ch_status()`
.. |close_cb| replace:: :vim:`close_cb`
.. |close_in| replace:: vpe.Channel.close_in`
.. |close| replace:: vpe.Channel.close`
.. |connect| replace:: vpe.Channel.connect`
.. |evalexpr| replace:: vpe.SyncChannel.evalexpr`
.. |getbufnr| replace:: vpe.Channel.getbufnr`
.. |info| replace:: vpe.Channel.info`
.. |JSChannel| replace:: `channels.JSChannel`
.. |JsonChannel| replace:: `channels.JsonChannel`
.. |log| replace:: vpe.Channel.log`
.. |NLChannel| replace:: `channels.NLChannel`
.. |on_close| replace:: vpe.Channel.on_close`
.. |on_connect| replace:: vpe.Channel.on_connect`
.. |on_message| replace:: vpe.Channel.on_message`
.. |open| replace:: vpe.Channel.open`
.. |RawChannel| replace:: `channels.RawChannel`
.. |read| replace:: vpe.Channel.read`
.. |sendexpr| replace:: vpe.SyncChannel.sendexpr`
.. |send| replace:: vpe.Channel.send`
.. |setoptions| replace:: vpe.Channel.setoptions`
.. |settimeout| replace:: vpe.Channel.settimeout`
.. |status| replace:: vpe.Channel.status`
.. |subprocess| replace:: subprocess_
.. |vch| replace:: vpe.Channel.vch`

The introduction of asynchronous I/O support in Vim 8.0, with channels and jobs
created many new possibilities for extending Vim with plug-ins. For example,
interfacing to a third party code quality server.

It also introduced new Vim script types that (currently) have no Python
equivalents. Also, it is advantageous to be able to use callback functions to
receive data in order to keep your plug-in responsive. This makes direct use
from Python non-trivial so VPE provides extensions to make things easier.


Status
======

VPE's support for channels is not yet particularly mature. However is is
functional and seems stable, and you should not feel discouraged from using the
current API.

There are a number of areas that zero or minimal support.

====================  ==========================================================
Vim function/feature  Status
====================  ==========================================================
Jobs                  No support. For quite a few use cases it is arguably
                      better to use Python |subprocess| module.
ch_readblob           Currently there is no way to read pure binary data. Even
                      you use a |RawChannel| Vim will replace NUL bytes with NL
                      (char 10) bytes.
ch_getbufnr           VPE does not really attempt to support associating buffers
                      with channels.
ch_logfile            Not supported, although ch_log is. This should *really* be
                      fixed.
ch_readraw            Not implemented, but it is arguably better to use
                      on_message to handle input. But I must admit, I have not
                      really given this much thought.
====================  ==========================================================

I am happy to receive suggestions about the best way to support the missing
features at https://github.com/paul-ollis/vim-vpe/issues.


The Channel class
=================

Introduction
------------

VPE provides the |Channel| and related classes as the basis for socket and pipe
I/O. A |Channel| provides a Pythonic, object oriented, interface to the various
Vim ``ch_...`` functions. |Channel| is a base class from which four API classes
are ultimately derived.

==================  ============================================================
|RawChannel|        Has an underlying Vim channel with mode == 'raw'.
|NLChannel|         Has an underlying Vim channel with mode == 'nl'.
|JSChannel|         Has an underlying Vim channel with mode == 'js'.
|JsonChannel|       Has an underlying Vim channel with mode == 'json'.
==================  ============================================================

Python code should use one of the above four classes.

Here is an approximate mapping from vim's functions to |Channel| methods.

.. _compatibility-table:

==================  ============================================================
Vim function        |Channel| method
------------------  ------------------------------------------------------------
|ch_open|           This is invoked when a |Channel| is created. A channel also
                    automatically keeps trying to connect until successful.
|ch_close_in|       |close_in|
|ch_close|          |close|
|ch_read|           |read|
|ch_readraw|        Not (yet) implemented, but the data delivered by
                    |on_message| is the same as ch_readraw provides.
|ch_readblob|       Not (yet) implemented.
|ch_sendraw|        |send|
|ch_evalexpr|       |evalexpr|. Only available for |JSChannel| and
                    |JsonChannel|.
|ch_sendexpr|       |sendexpr|. Only available for |JSChannel| and
                    |JsonChannel|.
|ch_evalraw|        Not (yet) supported.
|ch_getbufnr|       |getbufnr|
|ch_getjob|         Not (yet) supported
|ch_info|           |info|. Note that the id, port and sock_timeout values
                    are integers; not strings.
|ch_logfile|        Not (yet) implemented.
|ch_log|            |log|
|ch_setoptions|     The socket timeout can be set using |settimeout|. The mode
                    cannot be changed and the callback cannot be explicitly set.
|ch_status|         |status|
==================  ============================================================


Channel paradigm
----------------

The channel classes are intended to be used by inheritance. Below is some code
showing the basic pattern.

.. code-block:: python

    from vpe import channels

    class ServerChannel(channels.JsonChannel):
        """Interface to the server program."""

        def on_connect(self):
            """Handle a new outgoing connection."""

        def on_message(self, message: Any) -> None:
            """Handle a new incoming message.

            :message: The incoming, JSON-encoded message.
            """

    ch = ServerChannel('localhost:6789')

When the ``ServerChannel`` is created, a connection attempt is immediately made
(internally |ch_open| is invoked). If the connection attempt succeeds then the
|on_connect| method is invoked in the very near future (via |call_soon|).
Normally you use your |on_connect| method to perform any operations that need to
happen immediately upon a successful connection.

The |on_message| method is invoked whenever Vim's channel's input buffer
contains a complete message or, for a |RawChannel|, whenever any data is
received.

Messages are typically sent using the |sendexpr| method. Unformatted data can be
sent using |send|, but this will more typically be used with |RawChannel|
instances.

If the initial connection attempt does time out, the attempt can be retried
using the |connect| method. Sometimes using a timer to keep retrying is a good
approach.

.. code-block:: python

    class ServerChannel(channels.JsonChannel):
        """Interface to the server program."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.conn_timer = vpe.Timer(
                ms=1000, func=self.connect, repeat=-1, pass_timer=False)

        def on_connect(self):
            """Handle a new outgoing connection."""
            self.conn_timer.stop()

        ...

In the above example, the timer is set to fire every second forever. The
|connect| method can be invoked directly by the timer - |connect| does nothing
if the connection is already active. The |on_connect| method is a good place to
stop the timer running.

A |Channel| always sets the |callback| and |close_cb| options on the channel. So
incoming messages are handled asynchronously, invoking the |on_message| method.

The |close_cb| option is used by the |Channel| to properly clean things up. As
part of this cleanup the methods |on_close| and |close| are invoked in that
order. You can override |on_close| to perform any additional clean up; the
base class implementation does nothing.


Channel functions
=================

The |channels| module also provides a set of very thin wrapper around most of
the Vim 'ch\_...' functions. All those listed in the :ref:`mapping
table<compatibility-table>` above are provided, except for |ch_canread|,
|ch_readraw|, |ch_readblob|, |ch_open| and |ch_logfile|. These wrappers are
provided mainly for use by the |Channel| class, but you can use them in your own
code.

.. code-block:: python

    from vpe import channels


    class ServerChannel(channels.JsonChannel):
        ...

    ch = ServerChannel('localhost:6789')
    info = channels.ch_info(ch.vch)

The functions takes the same arguments as the built-in Vim functions except that
a Channel's |vch| attribute must be used in cases where the Vim function expects
a handle.

If you find it necessary to use any of these functions, please raise an issue
at https://github.com/paul-ollis/vim-vpe/issues, explaining why you could not
achieve you aim using only |Channel| class methods.
