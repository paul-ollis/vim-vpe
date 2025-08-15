"""Support for using Vim channels."""
# pylint: disable=deprecated-method

from typing import Set, Iterator, Tuple, Any
import asyncio
import json
import io
import threading
import time
import traceback

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support

_run_after = ['test_vim.py']


class Server(threading.Thread):
    """Simple server for channel testing."""
    server: asyncio.base_events.Server
    tasks: Set[asyncio.Task]
    addr: Tuple[str, int]
    loop: Any
    q: asyncio.Queue
    quitter: asyncio.Task

    def __init__(self, type='json', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = []
        self.running = False
        self.mode = 'eval'
        self.type = type

    def run(self):
        self.running = True
        asyncio.run(self.execute())

    async def execute(self):
        """Start serving using asyncio."""
        self.loop = asyncio.get_running_loop()
        self.q = asyncio.Queue()
        self.tasks = set()
        self.server = await asyncio.start_server(
            self.on_connect, host='localhost', port=8887)
        log.info(f'{self.server=}')
        self.addr = self.server.sockets[0].getsockname()
        log.info(f'Serving on {self.addr}')
        self.quitter = asyncio.create_task(self.wait_for_quit())
        try:
            async with self.server:
                await self.server.serve_forever()
        except asyncio.CancelledError:
            log.info('Serving cancelled')
        log.info('Wait for server to close cleanly')
        await self.server.wait_closed()
        log.info('Make all tasks quit.')
        await self.quit()
        log.info('Execution complete')

    async def wait_for_quit(self):
        await self.q.get()
        self.do_stop()
        await self.quit()

    def stop_tasks(self):
        """Stop all tasks."""
        for task in self.tasks:
            log.info(f'Stop task {task.get_name()}')
            task.cancel()

    async def quit(self):
        """Arrange to quit running."""
        while self.tasks:
            try:
                await self.tasks.pop()
            except asyncio.CancelledError:
                pass

    async def on_connect(
            self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Callback for new incoming connection.

        :reader: The new StreamReader for the connection.
        :writer: The new StreamWriter for the connection.
        """
        log.info('Incoming connection')
        handler = self.process_requests(reader, writer)
        self.tasks.add(asyncio.create_task(handler, name='process'))

    async def process_requests(
            self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Process incoming requests from a connection.

        :reader: The StreamReader for the connection.
        :writer: The StreamWriter for the connection.
        """
        buf = ''
        while True:
            data = await reader.read(1024)
            log.info(f'Read: {data!r}')
            if not data:
                log.info('Connection closed')
                return
            buf += data.decode()
            if self.type == 'raw':
                buf = await self.handle_raw(buf, writer)
            else:
                buf = await self.handle_json(buf, writer)

    async def handle_raw(self, buf, writer):
        resp = f'{buf}-resp'
        writer.write(resp.encode())
        await writer.drain()
        await asyncio.sleep(0.5)

        resp = f'resp'
        writer.write(resp.encode())
        await writer.drain()

        return ''

    async def handle_json(self, buf, writer):
        decoder = json.JSONDecoder()
        for buf, message in self.get_messages(decoder, buf):
            log.info(f'Message: {message!r}')
            self.messages.append(message)
            if self.mode in ('eval', 'close'):
                message[1] = message[1] + '-resp'
            elif self.mode == 'notify':
                message[0] = 0
                message[1] = message[1] + '-notify'
            else:
                fail(f'Invalid test server mode: {self.mode}')
            enc_message = json.dumps(message).encode()
            log.info(f'Resp: {enc_message!r}')
            writer.write(enc_message)
            await writer.drain()
            log.info("Resp drained")
            if self.mode == 'close':
                writer.close()
                await writer.wait_closed()

        return buf

    def stop(self):
        """Stop the server."""
        if self.running:
            self.loop.call_soon_threadsafe(self._stop)
            self.join()
            self.running = False

    def _stop(self):
        self.q.put_nowait(None)

    def do_stop(self):
        """Stop the server running."""
        log.info('Stopping the server')
        self.server.close()

    @staticmethod
    def get_messages(
            decoder: json.JSONDecoder, buf: str) -> Iterator[Tuple[str, Any]]:
        """Parse individual messages from an input buffer.

        :decoder: A json decoder.
        :buf:     The buffer to decode.
        :yield:   Tuples of (unused-buf, message).
        """
        message = 'dummy'
        while buf and message:
            message = ''
            try:
                message, index = decoder.raw_decode(buf)
            except json.JSONDecodeError:
                log.info(f'Decode error: {buf!r}')
                return
            except Exception:
                f = io.StringIO()
                traceback.print_exc(file=f)
                log.info(f.getvalue())
                raise

            buf = buf[index:].lstrip()
            yield buf, message


class Channel(support.Base):
    """Base for all channel tests."""


class JsonChannel(Channel):
    """JSON channels.

    Probably the easiest to use with Python.
    """
    server: Server

    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            from vpe import channels


            class MyChannel(channels.JsonChannel):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.messages = []
                    self.close_occurred = False

                def on_message(self, message):
                    self.messages.append(message)

                def on_close(self):
                    self.close_occurred = True


            ref_name = 'g:ch_ref'
            def save_ch_ref(ch):
                vim.command(f'let {ref_name} = {ch.vch.varname}')


            def ref_info(ch):
                if vim.eval(f'exists("{ref_name}")') == '1':
                    return {
                        'status': vim.eval(f'ch_status({ref_name})'),
                        'exists': vim.eval(f'exists("{ch.vch.varname}")'),
                    }
                return {}


            def ch_ref_close():
                vim.command(f'call ch_close({ref_name})')
        """
        super().suiteSetUp()
        self.run_self()

    def setUp(self):
        """Per test set up."""
        self.server = Server()

    def tearDown(self):
        """Per test clean up."""
        self.server.stop()

    def do_connect(self):
        """Perform connection request.

        :<py>:

            ch.connect()
            res.is_open = ch.is_open
            res.ch_id = ch.vch.chid
            dump(res)
        """
        return self.run_self()

    def do_continue(self):
        """Continue Vim session and collect received messages.

        :<py>:

            res.messages = ch.messages
            res.__dict__.update(ref_info(ch))
            res.close_occurred = ch.close_occurred
            dump(res)
        """
        return self.run_self()

    @test(testID='channel-connect-fail')
    def connect_fail(self):
        """A channel immediately attempts to connect, but fails gracefully.

        The connect method can be used to retry connecting.

        :<py>:

            ch = MyChannel('localhost:8887')

            res = Struct()
            res.is_open = ch.is_open

            dump(res)
        """
        res = self.run_self()
        failIf(res.is_open)
        self.server.start()
        res = self.do_connect()
        # TODO: Flakey: Have seen next line fail!
        failUnless(res.is_open)

    @test(testID='channel-connect-ok')
    def connect_ok(self):
        """A channel will connect to a waiting server.

        Calling connect on an already connected channel is null operation.

        :<py>:

            ch = MyChannel('localhost:8887')

            res = Struct()
            res.is_open = ch.is_open
            ch.connect()

            dump(res)
        """
        self.server.start()
        res = self.run_self()
        failUnless(res.is_open)

    @test(testID='channel-id')
    def channel_id(self):
        """The underyling channel ID is available.

        The ID is -1 if the last connect attempt failed.

        :<py>:

            ch = MyChannel('localhost:8887')

            res = Struct()
            res.ch_id = ch.vch.chid
            ch.close()
            res.ch_id_closed = ch.vch.chid

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.ch_id_closed, -1)
        self.server.start()
        res = self.do_connect()
        failUnless(res.ch_id >= 0)

    def create_channel(self):
        """Create a channel.

        :<py>:

            import gc, sys
            ch = MyChannel('localhost:8887')
        """
        self.run_self()

    @test(testID='channel-del')
    def channel_del(self):
        """When a channel is deleted, it is automatically closed.

        :<py>:

            res = Struct()

            vch = ch.vch
            res.info = ch.vch.info
            ref_name = 'g:ch_ref'
            vim.command(f'let {ref_name} = {vch.varname}')

            res.init_status = vim.eval(f'ch_status({ref_name})')

            del ch
            res.del_status = vim.eval(f'ch_status({ref_name})')
            res.ch_var_status = vim.eval(f'exists("{vch.varname}")')

            dump(res)
        """
        self.server.start()
        self.create_channel()
        res = self.run_self()
        failUnlessEqual('open', res.init_status)
        failUnlessEqual('closed', res.del_status)
        failUnlessEqual('0', res.ch_var_status)

    @test(testID='channel-send-receive')
    def send_receive(self):
        """A channel can be used to evaluate expressions.

        :<py>:

            ch = MyChannel('localhost:8887')

            res = Struct()
            res.messages = ch.messages
            resp = ch.evalexpr('Hello')
            res.resp = resp
            dump(res)
        """
        self.server.start()
        res = self.run_self()
        failUnlessEqual('Hello-resp', res.resp)

    @test(testID='channel-unsolicited-receive')
    def unsolicited_receive(self):
        """A channel can receive unsolicited messages

        The on_message callback is invoked when unsolicited messages are
        received.

        :<py>:

            ch = MyChannel('localhost:8887')

            res = Struct()
            res.messages = ch.messages
            resp = ch.sendexpr('Hello')
            res.resp = resp
            dump(res)
        """
        self.server.start()
        self.server.mode = 'notify'
        res = self.run_self()
        a = time.time()
        while time.time() - a < 0.5 and len(res.messages) < 1:
            self.control.delay(0.01)
            res = self.do_continue()
        failUnlessEqual(1, len(res.messages))

    @test(testID='channel-remote-close')
    def remote_close(self):
        """A remote close of channel invokes the on_close callback.

        The underlying Vim channel object is also released.

        :<py>:

            ch = MyChannel('localhost:8887')
            save_ch_ref(ch)

            res = Struct()
            res.messages = ch.messages
            resp = ch.evalexpr('Hello', timeout_ms=100)

            dump(res)
        """
        self.server.start()
        self.server.mode = 'close'
        self.run_self()
        res = self.do_continue()
        failUnlessEqual('closed', res.status)
        failUnlessEqual('0', res.exists)
        failUnless(res.close_occurred)

    @test(testID='channel-close-in')
    def channel_close_in(self):
        """The input half of a channel can be closed.

        :<py>:

            ch = MyChannel('localhost:8887')
            save_ch_ref(ch)

            res = Struct()
            res.ch_id = ch.vch.chid
            ch.close_in()

            dump(res)
        """
        self.server.start()
        self.run_self()
        # TODO: I do have not figured out how to verify that the close worked.
        #       This is just providing coverage.

    @test(testID='channel-query')
    def channel_query(self):
        """The getbufnr, status and info methods provide channel information.

        :<py>:

            ch = MyChannel('localhost:8887')

            res = Struct()

            res.buf_err = ch.getbufnr('err')
            res.buf_out = ch.getbufnr('out')
            res.buf = ch.getbufnr('')

            res.st_err = ch.status('err')
            res.st_out = ch.status('out')
            res.st = ch.status()

            res.orig_timeout = ch.info()['sock_timeout']
            ch.settimeout(3000)
            res.info = ch.info()

            dump(res)
        """
        self.server.start()
        res = self.run_self()
        # TODO: This is really just providing coverage.
        failUnlessEqual('-1', res.buf_err)
        failUnlessEqual('-1', res.buf_out)
        failUnlessEqual('-1', res.buf)

        failUnlessEqual('closed', res.st_err)
        failUnlessEqual('closed', res.st_out)
        failUnlessEqual('open', res.st)

        failUnlessEqual(2000, res.orig_timeout)
        failUnlessEqual('open', res.info['status'])
        failUnlessEqual(8887, res.info['port'])
        failUnlessEqual(3000, res.info['sock_timeout'])
        failUnlessEqual('localhost', res.info['hostname'])
        failUnless(isinstance(res.info['id'], int))

    @test(testID='channel-invalid-send')
    def invalid_send(self):
        """Invalid send attempts are handled.

        :<py>:

            ch = MyChannel('localhost:8887')
            save_ch_ref(ch)
            ch_ref_close()
            ch.sendexpr('Hello')

            res = Struct()
            dump(res)
        """
        self.server.start()
        self.run_self()
        # TODO: This is really just providing coverage.

    @test(testID='channel-log')
    def channel_log(self):
        """Using the channel log.

        :<py>:

            vim.ch_logfile(tmp_path('test-ch.log'), 'w')
            try:
                ch = MyChannel('localhost:8887')
                ch.log('hello')
            finally:
                vim.ch_logfile('')
            res = Struct()
            dump(res)
        """
        self.server.start()
        self.run_self()
        with open('/tmp/test-ch.log', 'rt') as f:
            lines = [line.rstrip() for line in f.readlines()]
        for line in lines:
            if line.endswith('hello'):
                break
        else:
            fail('Log message not found')


class RawChannel(Channel):
    """Raw channels.

    Vim does no encoding or decoding.
    """
    server: Server

    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            from vpe import channels


            class MyChannel(channels.RawChannel):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.messages = []
                    self.close_occurred = False

                def on_message(self, message):
                    self.messages.append(message)

                def on_close(self):
                    self.close_occurred = True


            ref_name = 'g:ch_ref'
            def save_ch_ref(ch):
                vim.command(f'let {ref_name} = {ch.vch.varname}')


            def ref_info(ch):
                if vim.eval(f'exists("{ref_name}")') == '1':
                    return {
                        'status': vim.eval(f'ch_status({ref_name})'),
                        'exists': vim.eval(f'exists("{ch.vch.varname}")'),
                    }
                return {}


            def ch_ref_close():
                vim.command(f'call ch_close({ref_name})')
        """
        super().suiteSetUp()
        self.run_self()

    def setUp(self):
        """Per test set up."""
        self.server = Server(type='raw')

    def tearDown(self):
        """Per test clean up."""
        self.server.stop()

    def do_recv(self):
        """Receive any incoming data on the test channel.

        :<py>:

            res.messages = ch.messages
            dump(res)
        """
        return self.run_self()

    @test(testID='channel-raw')
    def raw_channel(self):
        """Use of a raw channel.

        :<py>:

            ch = MyChannel('localhost:8887')

            res = Struct()
            res.messages = ch.messages
            resp = ch.send('Hello')

            res.messages = ch.messages
            res.resp = resp
            dump(res)
        """
        self.server.start()
        res = self.run_self()

        a = time.time()
        while time.time() - a < 5.0 and len(res.messages) < 2:
            self.control.delay(0.01)
            res = self.do_recv()
        failUnlessEqual(2, len(res.messages))
        failUnlessEqual(['Hello-resp', 'resp'], res.messages)

    @test(testID='channel-raw-bytes')
    def raw_channel_bytes(self):
        """Use of a raw channel and bytes.

        When bytes are provided, VPE converts the value to an an equivalent
        string (by decoding as latin-1).

        :<py>:

            ch = MyChannel('localhost:8887')

            res = Struct()
            res.messages = ch.messages
            resp = ch.send(b'Hello')

            res.messages = ch.messages
            res.resp = resp
            dump(res)
        """
        self.server.start()
        res = self.run_self()

        a = time.time()
        while time.time() - a < 5.0 and len(res.messages) < 2:
            self.control.delay(0.01)
            res = self.do_recv()
        failUnlessEqual(2, len(res.messages))
        failUnlessEqual(['Hello-resp', 'resp'], res.messages)

    @test(testID='channel-raw-explicit-read')
    def raw_channel_explicit_read(self):
        """Use of a raw channel, explicit read (not using callback).

        :<py>:

            ch = MyChannel('localhost:8887')

            res = Struct()
            res.messages = ch.messages
            ch.send('Hello')
            res.data = ch.read(timeout_ms=100)
            ch.messages = ['dummy']

            res.messages = ch.messages
            dump(res)
        """
        self.server.start()
        res = self.run_self()

        a = time.time()
        while time.time() - a < 5.0 and len(res.messages) < 1:
            self.control.delay(0.01)
        failUnlessEqual('Hello-resp', res.data)
