"""Support for using minirpyc for Vim control.

This was developed to support testing of VPE. It is used by the rpy_support
module. It is not intended to be directly imported by any other code.
"""
from __future__ import annotations

import functools
import re
import sys
import time
import traceback
from collections import deque
from typing import Any, Iterator, Optional, Tuple, Union

try:
    import vpe
except ImportError:
    import minirpyc
    from minirpyc.core.consts import MsgType
else:
    from vpe import minirpyc
    from vpe.minirpyc.core.consts import MsgType

brine = minirpyc.core.brine
consts = minirpyc.core.consts
brine = minirpyc.core.brine

slave_config = dict(
    allow_all_attrs=True,
    allow_pickle=True,
    allow_getattr=True,
    allow_setattr=True,
    allow_delattr=True,
    allow_exposed_attrs=False,
    import_custom_exceptions=True,
    instantiate_custom_exceptions=True,
    instantiate_oldstyle_exceptions=True,
)

R_OBJ = re.compile(r' object at 0x[A-Fa-f0-9]+')


class Indenter:                                              # pragma: no cover
    """Simple object to help indent trace essages by function call level."""
    def __init__(self, width=4):
        self.level = -1
        self.width = width

    @property
    def pad(self):
        """The padding for the current level."""
        return ' ' * max(0, self.level) * self.width

    def indents(self, func):
        """Decorate a function to increase level during the call."""
        @functools.wraps(func)
        def invoke(*args, **kwargs):
            self.level += 1
            try:
                return func(*args, **kwargs)
            finally:
                self.level -= 1

        return invoke


ind = Indenter()


def hex_data(data: bytes) -> str:                            # pragma: no cover
    """Generate a simple, truncated hex dump."""
    hex_str = data.hex(' ')
    if len(hex_str) <= 50:
        return hex_str
    return f'{hex_str[:50]}...'


def n_truncate(text: Union[str, bytes]) -> str:              # pragma: no cover
    """Truncate a string in a readable fashion."""
    if len(text) <= 50:
        return f'{len(text)}:{text}'
    return f'{len(text)}:{text[:50]}...'


def truncate(text: Union[str, bytes]) -> str:                # pragma: no cover
    """Truncate a string in a readable fashion."""
    text = R_OBJ.sub(' inst', text)
    if len(text) <= 70:
        return f'{text}'
    return f'{text[:50]}...'


class Reassembler:
    """A message reassembler."""
    # pylint: disable=too-few-public-methods

    def __init__(self):
        self.buf = b''
        self.messages = deque()

    def feed(self, data: bytes = '') -> Iterator[bytes]:
        """Feed the input buffer and yield complete messages."""
        try:
            self._feed(data)
        except Exception:                                    # pragma: no cover
            traceback.print_exc()
            raise

    # TODO: I do not see exceptions raised in this method.

    @ind.indents
    def _feed(self, data: bytes = ''):
        """Feed the input buffer, extracting complete messages."""
        # print(f'Feed: data={truncate(data)}')
        buf = self.buf + data
        while len(buf) >= 8:
            msg_len = int(buf[:8], 16)
            if msg_len + 8 > len(buf) :
                # print(f'           {msg_len=} {len(buf)=}')
                break

            msg, buf = buf[8 : 8 + msg_len], buf[8 + msg_len:]
            #print(f'           msg={truncate(msg)}')
            raw_bytes = bytes.fromhex(msg.decode('latin-1', errors='ignore'))
            self.messages.append(unpack_message(raw_bytes))
            # print(
            #     f'{ind.pad}Reassembled: {len(self.buf)=}'
            #     f' {len(self.messages)=}')

        self.buf = buf

    def empty(self):
        """Test if there are zero messages available."""
        return not self.messages

    def peek(self) -> Optional[Tuple[int, int, Any]]:
        """Return the next available message."""
        if self.messages:
            return self.messages[0]
        return None                                          # pragma: no cover

    def next_message(self) -> Optional[Tuple[MsgType, int, Any]]:
        """Return the next available message."""
        if self.messages:
            return self.messages.popleft()
        return None                                          # pragma: no cover


class Channel:
    """A channel."""

    def __init__(self, transport):
        self.transport = transport
        self.reassembler = Reassembler()

    def send_message(self, data: bytes):
        """Send data as a message (length + value)."""
        hdr = f'{len(data) * 2:08x}'
        msg = hdr + data.hex()
        self.transport.send_data(msg.encode('latin-1', errors='ignore'))

    def recv_data(self):
        """Receive available data."""
        return self.transport.recv_data()

    def close(self):
        """Just to keep RPYC happy."""
        # TODO: This prevents the full cleanup taking place. Currently I am
        #       preventing this because it involves async requests and use of
        #       __del__ methods.


def anon_ints(obj):                                          # pragma: no cover
    """Recusively convert large integers to an anonymous value."""
    if isinstance(obj, (list, tuple)):
        ret = [anon_ints(v) for v in obj]
        if isinstance(obj, list):
            return ret
        else:
            return tuple(ret)
    if isinstance(obj, int):
        if obj > 10000:
            return 31415

    return obj


def safe_repr(obj):                                          # pragma: no cover
    """A form of ``repr`` that safely handles Netref objects."""
    if isinstance(obj, minirpyc.core.netref.BaseNetref):
        return f'Netref: {anon_ints(obj.____id_pack__)}'
    else:
        return repr(anon_ints(obj))


def unpack_message(data: bytes) -> Tuple[consts.MsgType, int, Any]:
    """Unpack a brined message."""
    msg, seq, args = brine.load(data)
    return MsgType(msg), seq, args


class Connection(minirpyc.core.protocol.Connection):
    """A connection."""

    def __init__(self, root, channel, config=None, log_path=None):
        config = config or {}
        super().__init__(root, channel, config=config)
        self.l = None
        if log_path:                                         # pragma: no cover
            self.enable_logging(log_path)

    def enable_logging(self, path='/tmp/rpc.log'):           # pragma: no cover
        """Enable logging to /tmp/rpc.log or specified path."""
        self.l = open(path, 'wt', buffering=1, encoding='utf-8')
        sys.stdout = self.l

    def close(self):
        """Invoked by __del__.

        This does nothing. Its existence is enough to prevent unwanted Rpyc
        cleanup actions.
        """

    @ind.indents
    def sync_request(self, handler, *args):
        """Send a requests and block waiting for the response.

        This depends on each request being guaranteed a response, which I
        believe to be the case.
        """
        seq = next(self._seqcounter)
        self._send(MsgType.MSG_REQUEST, seq, (handler, self._box(args)))

        # Await the response.
        msg = None
        while msg is None:
            resp = self._receive_message()
            if resp is None:                                 # pragma: no cover
                # Remote end has probably cloded the connection.
                self._cleanup()
                return None

            msg, seq, args = resp
            if msg == MsgType.MSG_REQUEST:                   # pragma: no cover
                # Remote has to make a request before it can complete the
                # response.
                self.dispatch_request(seq, args)
                msg = None
                continue

            is_exc, obj = self.decode_message(*resp)

        if msg is not None:
            if is_exc:
                raise obj               # pylint: disable=raising-non-exception

            return obj

        return None                                          # pragma: no cover

    def _send(self, msg, seq, args):
        """Yada."""
        data = brine.dump((int(msg), seq, args))
        return self._channel.send_message(data)

    @ind.indents
    def _receive_message(self) -> Optional[bytes]:
        """Busy-wait for a complete message."""
        reassembler = self._channel.reassembler
        end_t = time.time() + 0.5
        while reassembler.empty() and time.time() < end_t:
            data = self._channel.recv_data()
            if data == b'':                                  # pragma: no cover
                return None
            else:
                reassembler.feed(data)

        message = reassembler.next_message()
        if not message:                                      # pragma: no cover
            print(f'{ind.pad}_receive_message: timed out')
        return message

    def dispatch_request(self, seq, raw_args):  # decode_message
        """Yada."""
        try:
            handler, args = raw_args
            args = self._unbox(args)
            res = self._HANDLERS[handler](self, *args)
        except:                                   # pylint: disable=bare-except
            traceback.print_exc(file=self.l)
            t, v, tb = sys.exc_info()
            self._last_traceback = tb
            logger = self._config["logger"]
            if logger and t is not StopIteration:            # pragma: no cover
                logger.debug("Exception caught", exc_info=True)
            if (t is SystemExit
                    and self._config["propagate_SystemExit_locally"]):
                raise                                        # pragma: no cover
            if (t is KeyboardInterrupt
                    and self._config["propagate_KeyboardInterrupt_locally"]):
                raise                                        # pragma: no cover
            self._send(MsgType.MSG_EXCEPTION, seq, self._box_exc(t, v, tb))
        else:
            self._send(MsgType.MSG_REPLY, seq, self._box(res))

    @ind.indents
    def decode_message(self, msg: MsgType, seq: int, args: Any):
        """Yada."""
        # print("Connection.decode_message")
        if msg == MsgType.MSG_REQUEST:                       # pragma: no cover
            self.dispatch_request(seq, args)
            return None, None

        elif msg == MsgType.MSG_REPLY:
            obj = self._unbox(args)
            return False, obj

        elif msg == MsgType.MSG_EXCEPTION:
            obj = self._unbox_exc(args)
            return True, obj

        raise ValueError(f'invalid message type: {msg!r}')   # pragma: no cover

    def log(self, *args):                                    # pragma: no cover
        """Log a message."""
        if self.l:
            print(*args, file=self.l)
            self.l.flush()
