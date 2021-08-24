Module vpe.channels
===================

.. py:module:: vpe.channels

Development of channel support.

Channel
-------

.. py:class:: vpe.channels.Channel(...)

    .. code::

        Channel(
                net_address: str,
                drop: Optional[str] = None,
                noblock: Optional[bool] = None,
                waittime: Optional[int] = None,

    Pythonic wrapper around a Vim channel.


    **Parameters**

    .. container:: parameters itemdetails

        *net_address*
            A network address of the form hostname:port.
        *drop*
            When to drop messages. Must be 'auto' or 'never'.
        *noblock*
            Set to true to prevent blocking on on write operations.
        *waittime*
            Time to wait for a connection to succeed.
        *timeout_ms*
            Time to wait for blocking request.


    **Attributes**

        .. py:attribute:: open

            True if the channel is currently open.

        .. py:attribute:: vch
            :type: VimChannel:

            The underlying `VimChannel` object.

    **Properties**

        .. py:method:: is_open() -> bool
            :property:

            Test whether the channel is open.

    **Methods**

        .. py:method:: vpe.channels.Channel.close() -> None

            Close the channel.

            Related vim function = :vim:`ch_close`.

        .. py:method:: vpe.channels.Channel.close_in() -> None

            Close the input part of the channel.

            Related vim function = :vim:`ch_info`.

        .. py:method:: vpe.channels.Channel.connect()

            If necessary, try to connect.

        .. py:method:: vpe.channels.Channel.getbufnr(what: str) -> int

            Get the number of the buffer thas is being used for *what*.

            Related vim function = :vim:`ch_getbufnr`.

            **Parameters**

            .. container:: parameters itemdetails

                *what*: str
                    The type of use. One of 'err', 'out' or an empty string.

        .. py:method:: vpe.channels.Channel.info() -> dict

            Get information about the channel.

            Related vim function = :vim:`ch_info`.

            **Return value**

            .. container:: returnvalue itemdetails

                A dictionary of information.

        .. py:method:: vpe.channels.Channel.log(msg: str) -> None

            Write a message to the channel log file (if open).

            Related vim function = :vim:`ch_log`. Note that this always provides
            the channel argument.

            **Parameters**

            .. container:: parameters itemdetails

                *msg*: str
                    The message to add to the log file.

        .. py:method:: vpe.channels.Channel.on_close()

            Handler for when channel is closed.

            Not invoked when the `close` method is used.

            Needs to be over-ridden in a subclass.

        .. py:method:: vpe.channels.Channel.on_connect()

            Handler for a new outgoing connection.

            May be over-ridden in a subclass.

        .. py:method:: vpe.channels.Channel.on_message(message: str)

            Handler for messages not explicitly handled by read methods.

            Needs to be over-ridden in a subclass.

            The contents of *message* depend on the type of the channel. Note that
            for a raw channel, this is invoked when any amount of the input data
            stream has been received. It is up to the application code to buffer
            and decode the stream's contents.

            **Parameters**

            .. container:: parameters itemdetails

                *message*: str
                    The received message. This is always a string, even for raw
                    channels. Vim replaces any NUL chracters with newlines, so pure
                    binary messages cannot be handled using on_message.

        .. py:method:: vpe.channels.Channel.read(timeout_ms: Optional[int] = None)

            Read any available input.

        .. py:method:: vpe.channels.Channel.send(message: Union[str, bytes]) -> None

            Send a message to the server.

            Related vim function = :vim:`ch_sendraw`.

            **Parameters**

            .. container:: parameters itemdetails

                *message*: typing.Union[str, bytes]
                    The message to send to the server. A bytes value is converted
                    to a Latin-1 string before sending.

        .. py:method:: vpe.channels.Channel.settimeout(timeout_ms: Optional[int] = None)

            Set the default teimout for the channel.

            Related vim function = :vim:`ch_setoptions`.

            **Parameters**

            .. container:: parameters itemdetails

                *timeout_ms*: typing.Optional[int]
                    Time to wait for blocking request.

        .. py:method:: vpe.channels.Channel.status(part: Optional[str] = None) -> str

            Get information about the channel.

            Related vim function = :vim:`ch_status`.

            **Parameters**

            .. container:: parameters itemdetails

                *part*: typing.Optional[str]
                    Which part of the channel to query; 'err' or 'out'.

            **Return value**

            .. container:: returnvalue itemdetails

                One of the strings 'fail', 'open', 'buffered' or 'closed'.

JSChannel
---------

.. py:class:: vpe.channels.JSChannel(...)

    .. code::

        JSChannel(
                net_address: str,
                drop: Optional[str] = None,
                noblock: Optional[bool] = None,
                waittime: Optional[int] = None,

    Pythonic wrapper around a Vim channel in javascript mode.

JsonChannel
-----------

.. py:class:: vpe.channels.JsonChannel(...)

    .. code::

        JsonChannel(
                net_address: str,
                drop: Optional[str] = None,
                noblock: Optional[bool] = None,
                waittime: Optional[int] = None,

    Pythonic wrapper around a Vim channel in json mode.

NLChannel
---------

.. py:class:: vpe.channels.NLChannel(...)

    .. code::

        NLChannel(
                net_address: str,
                drop: Optional[str] = None,
                noblock: Optional[bool] = None,
                waittime: Optional[int] = None,

    Pythonic wrapper for a newline based channel.

RawChannel
----------

.. py:class:: vpe.channels.RawChannel(...)

    .. code::

        RawChannel(
                net_address: str,
                drop: Optional[str] = None,
                noblock: Optional[bool] = None,
                waittime: Optional[int] = None,

    Pythonic wrapper for a raw channel.

SyncChannel
-----------

.. py:class:: vpe.channels.SyncChannel(...)

    .. code::

        SyncChannel(
                net_address: str,
                drop: Optional[str] = None,
                noblock: Optional[bool] = None,
                waittime: Optional[int] = None,

    Pythonic wrapper around a "json" or "js" channel.

    **Methods**

        .. py:method:: vpe.channels.SyncChannel.evalexpr(expr: Any,timeout_ms: Optional[int] = None) -> Any

            Evaluate an expression on the server.

            Related vim function = :vim:`ch_evalexpr`.

            **Parameters**

            .. container:: parameters itemdetails

                *expr*: typing.Any
                    The expression to send to the server for evaluation.
                *timeout_ms*: typing.Optional[int]
                    Max time to wait for a response. This overrides the
                    *timeout_ms* given at construction time.

        .. py:method:: vpe.channels.SyncChannel.sendexpr(...)

            .. code::

                sendexpr(
                        expr: Union[None, int, float, str, bool, List[Any], Dict[str, Any]]

            Send an expression to the server.

            Related vim function = :vim:`ch_sendexpr`.

            **Parameters**

            .. container:: parameters itemdetails

                *expr*: typing.Union[NoneType, int, float, str, bool, typing.List[typing.Any], typing.Dict[str, typing.Any]]
                    The expression to send to the server.

VimChannel
----------

.. py:class:: vpe.channels.VimChannel(varname: str)

    Simple proxy for a :vim:`Channel`.

    This manages keeping the underlying Vim channel object alive, by storing
    it in a global Vim variable.

    **Parameters**

    .. container:: parameters itemdetails

        *varname*
            The name of the a vim variable currently referencing the
            :vim:`Channel`.


    **Attributes**

        .. py:attribute:: varname

            The name of a Vim variable holding a reference to the underlying
            Vim channel object. This is provided for debugging purposes.

    **Properties**

        .. py:method:: chid()
            :property:

            The ID for this channel.

        .. py:method:: closed()
            :property:

            True of the channel could not be opened or has been closed.

        .. py:method:: info()
            :property:

            Get the information for a channel.

    **Methods**

        .. py:method:: vpe.channels.VimChannel.close()

            Mark as closed and release the underlying reference variable.