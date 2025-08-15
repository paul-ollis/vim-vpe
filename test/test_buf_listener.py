"""Support for listening for buffer changes.

VPE support is provided by the `add_listener` method of `Buffer` and
the `BufListener` class.
"""

# pylint: disable=deprecated-method
# pylint: disable=unused-wildcard-import,wildcard-import
# pylint: disable=wrong-import-order

# TODO:
#   1. Should have test that does not change whole lines. Not trivial because
#      changes using vim.buffer only generate change notifications for whole
#      lines.

from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support                             # pylint: disable=wrong-import-order
from vpe import diffs

_run_after = ['test_vim.py']


class TestBufListenerBase(support.Base):
    """Base class for all buffer listening tests."""

    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            class MyListener:
                def __init__(self):
                    self.changes = []

                def handle_changes(
                        self,
                        buf: vpe.Buffer,
                        start_lidx: int,
                        end_lidx: int,
                        added:int,
                        raw_changes=None,
                        ops=None,
                    ) -> None:
                    if raw_changes is not None:
                        raw_changes = [dict(el) for el in raw_changes]
                    self.changes.append(
                        (buf.number, start_lidx, end_lidx, added,
                        ops, raw_changes))

            buf = vim.current.buffer
        """
        super().suiteSetUp()
        self.run_suite_setup()

    def setUp(self):
        """Called to set up each test.

        :<py>:

            buf[:] = [
                'Line 1',
                'Line 2',
                'Line 3',
                'Line 4',
            ]
        """
        super().setUp()
        self.run_setup()


class AddingLines(TestBufListenerBase):
    """Detection of lines being added to a buffer."""

    @test(testID='listen-add-01')
    def add_line_at_end(self):
        """Add a single line at the end of the buffer.

        :<py>:

            res = Struct()
            listener = MyListener()
            buf.add_listener(listener.handle_changes, ops=False)
            buf.append('Line 5')
            vim.listener_flush(buf.number)
            res.changes = listener.changes
            res.buf_num = buf.number
            dump(res)
        """
        res = self.run_self()
        buf_num, start, end, added, *_ = res.changes[0]
        failUnlessEqual(res.buf_num, buf_num)
        failUnlessEqual(4, start)
        failUnlessEqual(4, end)
        failUnlessEqual(1, added)

    @test(testID='listen-add-02')
    def add_line_at_start(self):
        """Add a single line at the start of the buffer.

        :<py>:

            res = Struct()
            listener = MyListener()
            buf.add_listener(listener.handle_changes, ops=False)
            buf[0:0] = ['Line 0']
            vim.listener_flush(buf.number)
            res.changes = listener.changes
            res.buf_num = buf.number
            dump(res)
        """
        res = self.run_self()
        print(res.changes)
        failUnlessEqual(1, len(res.changes))
        buf_num, start, end, added, *_ = res.changes[0]
        failUnlessEqual(res.buf_num, buf_num)
        failUnlessEqual(0, start)
        failUnlessEqual(0, end)
        failUnlessEqual(1, added)

    @test(testID='listen-add-03')
    def add_line_in_middle(self):
        """Add a lines in the middle of the buffer.

        :<py>:

            res = Struct()
            listener = MyListener()
            buf.add_listener(listener.handle_changes, ops=False)
            buf[1:1] = ['Line X', 'Line Y']
            vim.listener_flush(buf.number)
            res.changes = listener.changes
            res.buf_num = buf.number
            dump(res)
        """
        res = self.run_self()
        print(res.changes)
        failUnlessEqual(1, len(res.changes))
        buf_num, start, end, added, *_ = res.changes[0]
        failUnlessEqual(res.buf_num, buf_num)
        failUnlessEqual(1, start)
        failUnlessEqual(1, end)
        failUnlessEqual(2, added)


class DeletingLines(TestBufListenerBase):
    """Detection of lines being added to a buffer."""

    @test(testID='listen-del-01')
    def del_first_line(self):
        """Delete the first line.

        :<py>:

            res = Struct()
            listener = MyListener()
            buf.add_listener(listener.handle_changes, ops=False)
            del buf[0:1]
            vim.listener_flush(buf.number)
            res.changes = listener.changes
            res.buf_num = buf.number
            dump(res)
        """
        res = self.run_self()
        buf_num, start, end, added, *_ = res.changes[0]
        failUnlessEqual(res.buf_num, buf_num)
        failUnlessEqual(0, start)
        failUnlessEqual(1, end)
        failUnlessEqual(-1, added)

    @test(testID='listen-del-02')
    def del_last_line(self):
        """Delete the last line.

        :<py>:

            res = Struct()
            listener = MyListener()
            buf.add_listener(listener.handle_changes, ops=False)
            del buf[3:]
            vim.listener_flush(buf.number)
            res.changes = listener.changes
            res.buf_num = buf.number
            dump(res)
        """
        res = self.run_self()
        buf_num, start, end, added, *_ = res.changes[0]
        failUnlessEqual(res.buf_num, buf_num)
        failUnlessEqual(3, start)
        failUnlessEqual(4, end)
        failUnlessEqual(-1, added)

    @test(testID='listen-del-03')
    def del_mid_lines(self):
        """Delete 2 middle lines.

        :<py>:

            res = Struct()
            listener = MyListener()
            buf.add_listener(listener.handle_changes, ops=False)
            del buf[1:3]
            vim.listener_flush(buf.number)
            res.changes = listener.changes
            res.buf_num = buf.number
            dump(res)
        """
        res = self.run_self()
        buf_num, start, end, added, *_ = res.changes[0]
        failUnlessEqual(res.buf_num, buf_num)
        failUnlessEqual(1, start)
        failUnlessEqual(3, end)
        failUnlessEqual(-2, added)


class VaryingLevelsOfDetail(TestBufListenerBase):
    """The detail provided in callbacks varies."""

    @test(testID='listen-buffer-raw')
    def raw_changes_can_be_provided(self):
        """The unmodified changes details can be provided to the callback.

        :<py>:

            res = Struct()
            listener = MyListener()
            buf.add_listener(
                listener.handle_changes, ops=False, raw_changes=True)
            del buf[1:3]
            vim.listener_flush(buf.number)
            res.changes = listener.changes
            res.buf_num = buf.number
            dump(res)
        """
        res = self.run_self()
        buf_num, start, end, added, ops, raw_changes = res.changes[0]
        failUnlessEqual(res.buf_num, buf_num)
        failUnlessEqual(1, start)
        failUnlessEqual(3, end)
        failUnlessEqual(-2, added)
        failUnless(ops is None)
        failIf(raw_changes is None)
        failUnlessEqual(
            {'lnum': 2, 'col': 1, 'added': -2, 'end': 4}, raw_changes[0])

    @test(testID='listen-buffer-raw-and-ops')
    def ops_and_raw_changes_can_be_provided(self):
        """The unmodified changes and ops can be provided to the callback.

        :<py>:

            res = Struct()
            listener = MyListener()
            buf.add_listener(
                listener.handle_changes, raw_changes=True)
            del buf[1:3]
            vim.listener_flush(buf.number)
            res.changes = listener.changes
            res.buf_num = buf.number
            dump(res)
        """
        res = self.run_self()
        buf_num, start, end, added, ops, raw_changes = res.changes[0]
        failUnlessEqual(res.buf_num, buf_num)
        failUnlessEqual(1, start)
        failUnlessEqual(3, end)
        failUnlessEqual(-2, added)
        failIf(ops is None)
        failIf(raw_changes is None)
        failUnlessEqual(
            {'lnum': 2, 'col': 1, 'added': -2, 'end': 4}, raw_changes[0])
        expected_op = diffs.Operation.create(lnum=2, end=4, added=-2, col=1)
        failUnless(isinstance(ops[0], diffs.DeleteOp))
        failUnlessEqual('delete', ops[0].name)
        failUnlessEqual(2, ops[0].count)
        failUnlessEqual('<DeleteOp:1.0-3,2>', repr(ops[0]))
        failUnlessEqual(expected_op, ops[0])

    @test(testID='listen-buffer-ops-add')
    def ops_can_be_provided(self):
        """The detailed ops can be provided to the callback - add lines.

        :<py>:

            res = Struct()
            listener = MyListener()
            buf.add_listener(listener.handle_changes)
            buf.append('Line 5')
            vim.listener_flush(buf.number)
            res.changes = listener.changes
            res.buf_num = buf.number
            dump(res)
        """
        # TODO: Vim -bug: I have seem Vim segfault when this test is run.
        res = self.run_self()
        buf_num, start, end, added, ops, raw_changes = res.changes[0]
        failUnlessEqual(res.buf_num, buf_num)
        failUnlessEqual(4, start)
        failUnlessEqual(4, end)
        failUnlessEqual(1, added)
        failIf(ops is None)
        failUnless(raw_changes is None)
        expected_op = diffs.Operation.create(lnum=5, end=5, added=1, col=1)
        failUnless(isinstance(ops[0], diffs.AddOp))
        failUnlessEqual('add', ops[0].name)
        failUnlessEqual('<AddOp:4.0-4,1>', repr(ops[0]))
        failUnlessEqual(1, ops[0].count)
        failUnlessEqual(expected_op, ops[0])

    @test(testID='listen-buffer-ops-modify')
    def ops_can_be_provided_modify(self):
        """The detailed ops can be provided to the callback - modify lines.

        :<py>:

            res = Struct()
            listener = MyListener()
            buf.add_listener(listener.handle_changes)
            buf[1:3] = ['Line X', 'Line Y']
            vim.listener_flush(buf.number)
            res.changes = listener.changes
            res.buf_num = buf.number
            dump(res)
        """
        res = self.run_self()
        buf_num, start, end, added, ops, raw_changes = res.changes[0]
        failUnlessEqual(res.buf_num, buf_num)
        failUnlessEqual(1, start)
        failUnlessEqual(3, end)
        failUnlessEqual(0, added)
        failIf(ops is None)
        failUnless(raw_changes is None)
        expected_op = diffs.Operation.create(lnum=2, end=4, added=0, col=1)
        failUnless(isinstance(ops[0], diffs.ChangeOp))
        failUnlessEqual('change', ops[0].name)
        failUnlessEqual('change', ops[0].name)
        failUnlessEqual('<ChangeOp:1.0-3>', repr(ops[0]))
        failUnlessEqual(0, ops[0].count)
        failUnlessEqual(expected_op, ops[0])

    @test(testID='listen-buffer-stop')
    def litening_can_be_stopped(self):
        """Listening can be stopped.

        :<py>:

            res = Struct()
            res.buf_num = buf.number

            listener = MyListener()
            listen_handle = buf.add_listener(listener.handle_changes)
            buf[1:3] = ['Line X', 'Line Y']
            vim.listener_flush(buf.number)
            res.changes = listener.changes

            listen_handle.stop_listening()
            buf[1] = 'Line Z'
            vim.listener_flush(buf.number)
            res.no_changes = listener.changes

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, len(res.changes))
        failUnlessEqual(1, len(res.no_changes))
