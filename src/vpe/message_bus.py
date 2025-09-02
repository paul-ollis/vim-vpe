"""A pub/sub style message bus.

This provides a mechanism for routing messages between Python objects within
a Vim session.

Client code retrieves a message bus using a suitable name, such as the name of
the plugin:<py>::

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
"""
from __future__ import annotations

import io
import time
import traceback
import queue
import weakref
from collections import defaultdict
from typing import Any, Callable, TypeAlias, TypeVar

import vpe

NO_RESPONDER = object()
INFO = False

_message_buses: dict[str, Bus] = {}

ClassT = TypeVar("ClassT", bound=type)
MessageCallback: TypeAlias = Callable[['SimpleMessage'], None]
MessageMatcher: TypeAlias = Callable[['SimpleMessage'], bool]

#: A message calback registration.
#:
#: A 3-tuple of the callback function, an optional message matching function
#: and a boolean flag indicating if the message handler is active.
CallbackRegistration: TypeAlias = tuple[
    MessageCallback, MessageMatcher | None, int]


class SimpleMessage:
    """A simple message that carries arbitrary data.

    It is typically easier to use `post_simple_message` rather than directly
    contructing instances of this class.

    :@name:
        A name for the message.
    :@args:
        An arbitrary object carrying the message's argument. It is common to
        make this a ``tuple``, which is what `Bus.post_simple_message` does.
    """
    def __init__(self, name: str, args: Any):
        self.name = name
        self.args = args
        self.post_time = time.time()
        self.bus: Bus | None = None

    def __str__(self) -> str:
        return f'SimpleMessage({self.name})'


class Bus:
    """A message bus.

    This implements a form of pub/sub pattern.
    """
    def __init__(self, name: str):
        self._name = name
        self._message_queue: queue.Queue[SimpleMessage] = queue.SimpleQueue()
        self._registered_callbacks: dict[
            str, list[CallbackRegistration]] = defaultdict(list)
        self.my_proxy = weakref.proxy(self)
        self._process_cycle_pending: bool = False

    def post(self, message: SimpleMessage) -> None:
        """Post a message onto the bus."""
        message.bus = self.my_proxy
        self._message_queue.put(message)
        self._schedule_process_cycle()

    def post_simple_message(self, name: str, *args: Any) -> None:
        """Create and post a `SimpleMessage`.

        This is basically a convience method for:<py>::

            message = SimpleMessage(name, args)
            bus.post(message)
        """
        message = SimpleMessage(name, args)
        self.post(message)

    def subscribe(
            self,
            name: str,
            callback: MessageCallback,
            predicate: MessageMatcher | None = None,
        ) -> None:
        """Subscribe to a named message.

        :name:
            The name of the message being subscribed to.
        :callback:
            The function to be invoked when a matching message is received. The
            function is invoked with the matching message and the `Bus`
            instance.
        :predicate:
            A function that is invoked to (further) filter which messages are
            passed to the callback.
        """
        self._registered_callbacks[name].append((callback, predicate, True))
        if INFO:
            if predicate:
                print(f'Subcription: {name} -> {predicate}:{callback}')
            else:
                print(f'Subcription: {name} -> {callback}')

    def _schedule_process_cycle(self):
        """Schedule a message processing cycle using `vpe.call_soon."""
        if not self._process_cycle_pending:
            self._process_cycle_pending = True
            vpe.call_soon(self._process_queued_messages)

    def _process_queued_messages(self):
        """Process any queued messages.

        This is invoked by as a `vpe.call_soon`, which makes message processing
        pseudo-asynchronous.
        """
        # Clear the cycle pending flag before triggering any callbacks and
        # empty the queue because callbacks may add further messages, which we
        # want to ddefer to the next processing cycle.
        self._process_cycle_pending = False
        messages = []
        while not self._message_queue.empty():
            messages.append(self._message_queue.get())

        # Now invoke the callback for each queued message.
        for message in messages:
            if INFO:
                print(f'Bus[{self._name}]: received {message}')
            callbacks = self._registered_callbacks[message.name]
            for i, (callback, predicate, ok) in enumerate(callbacks):
                if not ok:
                    continue
                message.bus = self
                if predicate is None or predicate(message):
                    if INFO:
                        print(f'    forward to {callback}')
                    try:
                        callback(message)
                    except Exception as exc:  # pylint: disable=broad-exception-caught
                        s = []
                        s.append(
                            f'    forward failed for {callback} (disabling)')
                        s.append(f'    {exc}')
                        f = io.StringIO()
                        traceback.print_exception(exc, file=f)
                        s.extend(f.getvalue().splitlines())
                        callbacks[i] = callback, predicate, False
                        print('\n'.join(s))


def handle_message(name: str):
    """Mark a method as a message handler.

    :name: The name of the message to be handled.
    """
    def decorate(func: Callable[[SimpleMessage], None]):
        handled = getattr(func, '_handled_messages_', [])
        handled.append(name)
        setattr(func, '_handled_messages_', handled)
        return func

    return decorate


def install_message_handlers(obj: object, bus_name: str) -> None:
    """Install a handler for a given class instance."""
    bus = named_message_bus(bus_name)

    for name in dir(obj):
        method = getattr(obj.__class__, name, None)
        if not callable(method):
            continue
        method = getattr(obj, name, None)
        handled = getattr(method, '_handled_messages_', [])
        for message_name in handled:
            bus.subscribe(message_name, method)


def named_message_bus(name: str) -> Bus:
    """Create or retrieve the message bus with a given name.

    The first time this is invoked with a given name a new `Bus` instance is
    created. Subsequent calls with the same name retrieve the same `Bus`
    instance.

    :name:
        The name of the bus.
    """
    if name not in _message_buses:
        _message_buses[name] = Bus(name)
    return _message_buses[name]
