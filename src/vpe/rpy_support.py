"""Support for remote control of Vim using a connection.

This was developed to support testing ov VPE. It uses a very cut-down fork of
RPyC (https://rpyc.readthedocs) to allow external Python scripts almost
seamless control of Vim.
"""
from __future__ import annotations

import re
from pathlib import Path

import vpe
from vpe import channels, minirpyc, rpyc_support
from vpe.minirpyc.core.consts import MsgType
from vpe import vim

truncate = rpyc_support.truncate
ind = rpyc_support.ind


def as_bytes(buf: str | bytes) -> bytes:
    """Convert string buffer to bytes but leave a bytes buffer unchanged.

    If the argument is a string then this does a character-by-character
    conversion that is only guaranteed to produce correct results if the
    following is true:<py>:

        all(0 <= ord(c) <= 255 for s in buf])
    """
    if isinstance(buf, str):
        return buf.encode('latin-1', errors='ignore')
    else:                                                    # pragma: no cover
        return buf


class RemoteControlChannel(channels.RawChannel):
    """A Vim channel that supports remote control.

    This provides the socket I/O support required by the MiniRPyC library.
    """
    root: minirpyc.core.service.ClassicService
    chan: rpyc_support.Channel
    conn: rpyc_support.Connection

    def __init__(self, *args, **kwargs):
        """Yada."""
        super().__init__(*args, **kwargs)

    def on_connect(self):
        """Respond to a successful connection indication.

        This sets up the miniRPyC objects that handle the details of
        transparent RPC.
        """
        # temp_dir = os.environ.get('TEMP', '/tmp')
        self.root = minirpyc.core.service.ClassicService()
        self.chan = rpyc_support.Channel(self)
        self.conn = rpyc_support.Connection(
            self.root, self.chan, rpyc_support.slave_config)
            # log_path=f'{temp_dir}/vim_rpy.log')

    @ind.indents
    def on_message(self, message: bytes | str):
        """Yada."""
        data = as_bytes(message)
        reassembler = self.chan.reassembler
        # print(f'Recv: data={data[:8]}:{data[8:]}')
        reassembler.feed(data)
        if not reassembler.empty():
            msg, *_ = reassembler.peek()
            if msg == MsgType.MSG_REQUEST:
                msg, seq, args = reassembler.next_message()
                self.conn.dispatch_request(seq, args)

    def send_data(self, data: bytes) -> None:
        """Send data on behalf of miniRPyC."""
        super().send(data)

    # Forcing this code to be invoked is too hard.
    def recv_data(self):                                     # pragma: no cover
        """Receive available data.

        This can be invoked by rpyc_support.Connection._receive_message, but
        only when a complete message has not already been re-assembled by
        `on_message`.
        """
        s = self.read()
        if s:
            return s.encode('latin-1', errors='ignore')

        return b''


class RemoteControlServer:
    """A server that allows remote control using Python.

    Since Vim does not support listening for connections, the client
    application must listen for and accept the connection.

    :service_name:
        The nmeame of the service. This is used to get the port number from the
        ``~/.local/etc/services`` file.
    :waittime:
        How long (ms) to wait for a connection attempt to complete. Note that
        Vim will occasionally block (or at least become very unresponsive) for
        this length of time so zero is often the best value.
    :host:
        The host the should be connected to, defaults to localhost.
    :add_servername:
        If ``True`` and v:servername has the default form, add the number from
        v:servername.
    """
    def __init__(
            self,
            service_name: str,
            waittime: int = 1,
            host: str = 'localhost',
            add_servername: bool = False,
        ):
        port = _get_service_port(service_name, add_servername=add_servername)
        if port >= 0:
            self.timer = vpe.Timer(
                ms=1000,
                func=self.try_to_connect,
                repeat=-1,
                pass_timer=False)
            self.channel = RemoteControlChannel(
                net_address=f'{host}:{port}',
                drop='never',
                waittime=waittime)

    def try_to_connect(self):
        """Attempt to connect to the 'client'.

        Although this is providing the remote control service, Vim only
        supports initiating connections. So this timer function periodically
        attempts to connect to a 'client' that is listening for a connection.
        """
        channel = self.channel
        if not channel.is_open:                              # pragma: no cover
            # TODO: Not used by test support code. Specific testing is
            #       required.
            channel.connect()
            if channel.is_open:
                self.timer.stop()

    def close(self):
        """Close down the channel for this server.

        This closes the associated Vim socket channel. This is performed using
        call_soon so that the RPyC protocol completes before the channel is
        terminated.

        This instance is not usable for remote control after this.
        """
        self.timer.stop()
        vpe.call_soon(self.channel.close)


def _get_service_port(name: str, add_servername: bool = False) -> int:
    """Get the port for a named service.

    :name:
        The name of the service. This is used to get the port number from the
        ``~/.local/etc/services`` file.
    :add_servername:
        If ``True`` and v:servername has the default form, add the number from
        v:servername.
    """
    serv_path = Path('~/.local/etc/services').expanduser()
    with serv_path.open(mode='rt', encoding='utf-8') as f:
        for rawline in f:
            line = rawline.strip()
            if not line or line.startswith('#'):
                continue
            service_name, port_proto, *_ = line.split()
            port_str, *_ = port_proto.split('/')
            if service_name == name:
                port = int(port_str)
                break
        else:
            return -1

    if add_servername:
        print("ADD", vim.vvars.servername)
        m = re.match(r'G?VIM([0-9]+)', vim.vvars.servername)
        if m:
            port += int(m.group(1))
    print("CONN", port)
    return port
