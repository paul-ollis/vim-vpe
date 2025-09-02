.. IMPORTANT: This is an auto-generated file.

Module vpe.message_bus
======================


.. py:module:: message_bus

A pub/sub style message bus.

This provides a mechanism for routing messages between Python objects within
a Vim session.

Client code retrieves a message bus using a suitable name, such as the name of
the plugin:

.. code-block:: py

    bus = message_bus.named_message_bus('my-plugin-name')

The `Bus.post`, `Bus.post_simple_message` and `Bus.subscribe` methods are used
to send and receive messages. Subscribers receive messages vai callbacks that
invoked by `vpe.call_soon`.

Each messages is identified by a name, which is a simple string. Client code
subscribes to message using message names. All naming
convention choices are up to the client code, the message bus code simply uses
message names as keys that map to subscribers.

For most applications all messages can simply be instances of the
`SimpleMessage` class created and posted using `Bus.post_simple_message`.

.. rubric:: Bus

.. py:class:: Bus(name: str)

    A message bus.

    This implements a form of pub/sub pattern.

    **Methods**

        .. py:method:: post(message: SimpleMessage) -> None

            Post a message onto the bus.

        .. py:method:: post_simple_message(name: str, *args: Any) -> None

            Create and post a `SimpleMessage`.

            This is basically a convience method for:

            .. code-block:: py

                message = SimpleMessage(name, args)
                bus.post(message)

        .. py:method:: subscribe(...)

            .. code::

                subscribe(
                        name: str,
                        callback: MessageCallback,
                        predicate: MessageMatcher | None = None

            Subscribe to a named message.


            **Parameters**

            .. container:: parameters itemdetails

                *name*: str
                    The name of the message being subscribed to.
                *callback*: Callable
                    The function to be invoked when a matching message is received. The
                    function is invoked with the matching message and the `Bus`
                    instance.
                *predicate*: Optional
                    A function that is invoked to (further) filter which messages are
                    passed to the callback.

.. rubric:: SimpleMessage

.. py:class:: SimpleMessage(name: str, args: Any)

    A simple message that carries arbitrary data.

    It is typically easier to use `post_simple_message` rather than directly
    contructing instances of this class.

    **Parameters**

    .. container:: parameters itemdetails

        *name*
            A name for the message.
        *args*
            An arbitrary object carrying the message's argument. It is common to
            make this a ``tuple``, which is what `Bus.post_simple_message` does.

    **Attributes**

        .. py:attribute:: args

            An arbitrary object carrying the message's argument. It is common to
            make this a ``tuple``, which is what `Bus.post_simple_message` does.

        .. py:attribute:: name

            A name for the message.

.. rubric:: handle_message

.. py:function:: handle_message(name: str)

    Mark a method as a message handler.


    **Parameters**

    .. container:: parameters itemdetails

        *name*: str
            The name of the message to be handled.

.. rubric:: install_message_handlers

.. py:function:: install_message_handlers(obj: object, bus_name: str) -> None

    Install a handler for a given class instance.

.. rubric:: named_message_bus

.. py:function:: named_message_bus(name: str) -> Bus

    Create or retrieve the message bus with a given name.

    The first time this is invoked with a given name a new `Bus` instance is
    created. Subsequent calls with the same name retrieve the same `Bus`
    instance.

    **Parameters**

    .. container:: parameters itemdetails

        *name*: str
            The name of the bus.