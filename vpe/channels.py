"""Development of channel support."""

from typing import Any, Optional, Tuple, Dict, ClassVar, Union, List
from functools import partial
import weakref

from . import common
from . import core
from . import wrappers

__all__ = ['RawChannel', 'JsonChannel', 'NLChannel', 'JSChannel', 'VimChannel']

_VIM_FUNC_DEFS = """
function! VPEReadCallback(channel, message)
    let g:VPE_read_channel_info = ch_info(a:channel)
    let g:VPE_read_message = a:message
    call py3eval('vpe.channels.Channel._on_message()')
endfunction

function! VPECloseCallback(channel)
    let g:VPE_read_channel_info = ch_info(a:channel)
    call py3eval('vpe.channels.Channel._on_close()')
endfunction
"""

wrappers.vim.command(_VIM_FUNC_DEFS)

# Types for annotations.
JSONObject = Dict[str, Any]
JSONArray = List[Any]
JSONEncodable = Union[None, int, float, str, bool, JSONArray, JSONObject]

# Seems mypy cannot handle this yet.
# JSONEncodable = Union[None, int, float, str, bool, "JSONArray", "JSONObject"]
# JSONObject = Dict[str, "JSONEncodable"]
# JSONArray = List[JSONEncodable]


class VimChannel:
    """Simple proxy for a :vim:`Channel`.

    This manages keeping the underlying Vim channel object alive, by storing
    it in a global Vim variable.

    :varname: The name of the a vim variable currently referencing the
              :vim:`Channel`.

    @varname: The name of a Vim variable holding a reference to the underlying
              Vim channel object. This is provided for debugging purposes.
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, varname: str):
        self.varname = ''
        if varname == '':
            return
        status = wrappers.vim.eval(f'ch_status({varname})')
        if status != 'open':
            return

        info = wrappers.vim.eval(f'ch_info({varname})')
        self.varname = f'g:VPE_channel_{info["id"]}'
        wrappers.vim.command(f'let {self.varname} = {varname}')

    def close(self):
        """Mark as closed and release the underlying reference variable."""
        if self.varname:
            wrappers.vim.command(f'unlet {self.varname}')
            self.varname = ''

    @property
    def info(self):
        """Get the information for a channel."""
        if self.varname:
            return wrappers.vim.eval(f'ch_info({self.varname})')
        return {}

    @property
    def chid(self):
        """The ID for this channel."""
        return int(self.info.get('id', -1))

    @property
    def closed(self):
        """True of the channel could not be opened or has been closed."""
        return self.info.get('status') != 'open'


def literal_string(pystr: str) -> str:
    """Format a Python string as a Vim literal string.

    The result is enclosed in single quotes and any contained single quotes are
    doubled-up.

    :pystr: The string to quote.
    """
    text = pystr.replace("'", "''")
    return f"'{text}'"


def vim_repr(obj: Any) -> str:
    """Convert value to form usable in a Vim command.

    Special handling is provided for a number of types.

    :obj: The value to represent.
    """
    if isinstance(obj, VimChannel):
        return obj.varname
    if isinstance(obj, dict):
        body = ', '.join(
            f'{literal_string(key)}: {vim_repr(value)}'
            for key, value in obj.items())
        return '{' + body + '}'
    if isinstance(obj, str):
        return literal_string(obj)
    return str(obj)


class ChannelFunction:
    """A wrapper around a Vim channel function.

    This is used for all channel functions that take any :vim:`Channel`
    arguments.

    :name: The channel function name.
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, name: str):
        self.name = name

    def __call__(self, *args, **kwargs):
        call_and_assign(common.RET_VAR, self.name, *args)
        return core.coerce_arg(wrappers.vim.eval(common.RET_VAR))


def call_and_assign(varname: str, funcname: str, *args: Any) -> None:
    """Invoke a Vim function and assign the result to a Vim variable.

    This implements the invocation by forming a Vim command and executing it.
    This is not the most efficient way to invoke most vim functions, but is
    necessary when certain Vim types (such as :vim:`Channel` and :vim:`Job`)
    are involved.

    :varname:  The name of the variable accepting the return value.
    :funcname: The name of the function to invoke.
    :args:     The argumens for the function.
    """
    vim_args = [vim_repr(arg) for arg in args]
    cmd = f'let {varname} = {funcname}({", ".join(vim_args)})'
    wrappers.vim.command(cmd)


# Future: Consider whether readblob should be implemented.
class Channel:
    """Pythonic wrapper around a Vim channel.

    :net_address: A network address of the form hostname:port.
    :drop:        When to drop messages. Must be 'auto' or 'never'.
    :noblock:     Set to true to prevent blockon on write operations.
    :waittime:    Time to wait for a connection to succeed.
    :timeout_ms:  Time to wait for blocking request.

    @open: True if the channel is currently open.
    @vch: The underlying `VimChannel` object.
    """
    # pylint: disable=too-few-public-methods
    _mode_arg: str = 'raw'
    channels: ClassVar[Dict[int, weakref.ref]] = {}
    vim_channels: ClassVar[Dict[int, VimChannel]] = {}
    vch: VimChannel

    def __init__(                          # pylint: disable=too-many-arguments
            self, net_address: str, drop: Optional[str] = None,
            noblock: Optional[bool] = None, waittime: Optional[int] = None,
            timeout_ms: Optional[int] = None):
        self.net_address = net_address
        options = self._build_options(
            ('drop', drop), ('noblock', noblock), ('waittime', waittime),
            ('timeout', timeout_ms))
        options['mode'] = self._mode_arg

        # TODO: This does not handle responses to ch_sendexpr! Vim docs say it
        #       should, Vim code disagrees.
        options['callback'] = 'VPEReadCallback'
        options['close_cb'] = 'VPECloseCallback'
        self._open_options = options
        self.vch = VimChannel('')
        self.connect()

    def connect(self):
        """If necessary, try to connect."""
        if self.is_open:
            return
        try:
            call_and_assign(
                common.RET_VAR, 'ch_open', self.net_address,
                self._open_options)
        except common.VimError:                              # pragma: no cover
            return

        self.vch = VimChannel(common.RET_VAR)
        if self.vch.closed:
            return

        my_ref = weakref.ref(self, partial(self._on_del, self.vch.chid))
        self.channels[self.vch.chid] = my_ref
        self.vim_channels[self.vch.chid] = self.vch
        self.on_connect()

    @property
    def is_open(self) -> bool:
        """Test whether the channel is open."""
        return bool(self.vch) and not self.vch.closed

    @classmethod
    def _on_del(cls, chid, _ref):
        """Handler for when a vim channel is about to be finalized."""
        vch = cls.vim_channels.pop(chid)
        try:
            ch_close(vch)
        except common.VimError:                              # pragma: no cover
            pass
        cls.channels.pop(chid)

    @classmethod
    def _on_message(cls):
        """Handler for all messages from all channels."""
        ch = cls._get_active_channel()
        if ch is not None:
            ch.on_message(core.coerce_arg(wrappers.vim.vars.VPE_read_message))

    @classmethod
    def _on_close(cls):
        """Handler for when any channel is (remotely?) closed."""
        ch = cls._get_active_channel()
        if ch is not None:
            ch.on_close()
            ch.close()

    @classmethod
    def _get_active_channel(cls) -> Optional["Channel"]:
        """Get the Channel instance for the current callback."""
        ref = cls.channels.get(wrappers.vim.vars.VPE_read_channel_info['id'])
        return None if ref is None else ref()

    def on_connect(self):
        """Handler for a new outgoing connection.

        May be over-ridden in a subclass.
        """

    def on_message(self, message: Any):
        """Handler for messages not explicitly handled by read methods.

        Needs to be over-ridden in a subclass.

        The contents of *message* depend on the type of the channel. Note that
        for a raw channel, this is invoked when any amount of the input data
        stream has been received. It is up to the application code to buffer
        and decode the stream's contents.

        :message: The received message.
        """

    def on_close(self):
        """Handler for when channel is closed.

        Not invoked when the `close` method is used.

        Needs to be over-ridden in a subclass.
        """

    def close(self) -> None:
        """Close the channel.

        Related vim function = :vim:`ch_close`.
        """
        if self.vch.varname:
            ch_close(self.vch)

    def close_in(self) -> None:
        """Close the input part of the channel.

        Related vim function = :vim:`ch_info`.
        """
        ch_close_in(self.vch)

    def getbufnr(self, what: str) -> int:
        """Get the number of the buffer for use defined by *what*.

        Related vim function = :vim:`ch_getbufnr`.

        :what: The type of use. One of 'err', 'out' or an empty string.
        """
        return ch_getbufnr(self.vch, what)

    def info(self) -> dict:
        """Get information about the channel.

        Related vim function = :vim:`ch_info`.

        :return: A dictionary of information.
        """
        info = ch_info(self.vch)
        for name in ('id', 'port', 'sock_timeout'):
            if name in info:
                info[name] = int(info[name])
        return info

    def send(self, message: Any) -> None:
        """Send a message to the server.

        Related vim function = :vim:`ch_sendraw`.

        :message: The message to send to the server.
        """
        ch_sendraw(self.vch, message)

    def settimeout(self, timeout_ms: Optional[int] = None):
        """Set the default teimout for the channel.

        Related vim function = :vim:`ch_setoptions`.

        :timeout_ms: Time to wait for blocking request.
        """
        options = self._build_options(('timeout', timeout_ms),)
        ch_setoptions(self.vch, options)

    def status(self, part: Optional[str] = None) -> str:
        """Get information about the channel.

        Related vim function = :vim:`ch_status`.

        :part:   Which part of the channel to query; 'err' or 'out'.
        :return: One of the strings 'fail', 'open', 'buffered' or 'closed'.
        """
        options = self._build_options(('part', part))
        return ch_status(self.vch, options)

    def log(self, msg: str) -> None:
        """Write a message to the channel log file (if open).

        Related vim function = :vim:`ch_log`. Note that this always provides
        the channel argument.

        :msg:    The message to add to the log file.
        """
        ch_log(msg, self.vch)

    @staticmethod
    def _build_options(*pairs: Tuple[str, Any]) -> Dict[str, Any]:
        options = {}
        for name, value in pairs:
            if value is not None:
                options[name] = value
        return options


class SyncChannel(Channel):
    """Pythonic wrapper around a "json" or "js" channel."""

    def evalexpr(self, expr: Any, timeout_ms: Optional[int] = None) -> Any:
        """Evaluate an expression on the server.

        Related vim function = :vim:`ch_evalexpr`.

        :expr:       The expression to send to the server for evaluation.
        :timeout_ms: Max time to wait for a response. This overrides the
                     *timeout_ms* given at construction time.
        """
        options = self._build_options(('timeout', timeout_ms))
        return ch_evalexpr(self.vch, expr, options)

    def sendexpr(self, expr: JSONEncodable) -> None:
        """Send an expression to the server.

        Related vim function = :vim:`ch_sendexpr`.

        :expr: The expression to send to the server.
        """
        if not self.is_open:
            return
        options = {'callback': 'VPEReadCallback'}
        try:
            ch_sendexpr(self.vch, expr, options)
        except common.VimError as e:                         # pragma: no cover
            # This is just in case. It should not be possible for this to
            # occur.
            core.log(e)


class RawChannel(Channel):
    """Pythonic wrapper for a raw channel."""
    _mode_arg: str = 'raw'


class NLChannel(Channel):
    """Pythonic wrapper for a newline based channel."""
    _mode_arg: str = 'nl'


class JsonChannel(SyncChannel):
    """Pythonic wrapper around a Vim channel in json mode."""
    _mode_arg: str = 'json'


class JSChannel(SyncChannel):
    """Pythonic wrapper around a Vim channel in javascript mode."""
    _mode_arg: str = 'js'


def ch_close(vch: VimChannel):
    """Close a channel.

    :vch: The VimChannel wrapper of the underlying Vim channel object.
    """
    try:
        vim_ch_close(vch)
    except common.VimError as e:
        core.log(e)
    vch.close()


# Create the wrapped channel functions.
#
# Note that ch_canread, ch_read, ch_readraw, ch_readblob, ch_open and
# ch_logfile are not part of this set.
ch_evalexpr = ChannelFunction('ch_evalexpr')
vim_ch_close = ChannelFunction('ch_close')
ch_close_in = ChannelFunction('ch_close_in')
ch_evalexpr = ChannelFunction('ch_evalexpr')
ch_evalraw = ChannelFunction('ch_evalraw')
ch_getbufnr = ChannelFunction('ch_getbufnr')
ch_info = ChannelFunction('ch_info')
ch_sendexpr = ChannelFunction('ch_sendexpr')
ch_sendraw = ChannelFunction('ch_sendraw')
ch_setoptions = ChannelFunction('ch_setoptions')
ch_status = ChannelFunction('ch_status')
ch_log = ChannelFunction('ch_log')
