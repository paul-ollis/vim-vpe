"""Various of the extensions in VPE."""
# pylint: disable=deprecated-method
# pylint: disable=too-many-lines
# pylint: disable=wrong-import-order

import os
import platform
import re
import time
from pathlib import Path

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.DataMaker import literalText2Text
from cleversheep3.Test.Tester import *

import support
import vim_if
from support import fix_path

import vpe
from vpe import utils

_run_after = ['test_vim.py', 'test_mapping_x.py']


class TestInfo(support.Base):
    """General information features."""
    @test(testID='version')
    def version(self):
        """VPE provides a __version__ string.

        :<py>:
            res = Struct()
            res.version = vpe.__version__
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('0.7.0', res.version)


class DisplayBuffer(support.Base):
    """Special display buffer.

    This is a buffer configured to be under (Python) plugin code control. It is
    useful for displaying information without allowing the user to
    accidentally edit it.
    """

    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            from vpe import commands
        """
        super().suiteSetUp()
        self.run_suite_setup()

    def suiteTearDown(self):
        """Called to cleanup after the suite ends.

        :<py>:

            commands.wincmd('o')
            commands.buffer('1')
        """
        super().suiteTearDown()
        self.run_suite_teardown()

    def setUp(self):
        """Per test set up.

        :<py>:

            commands.wincmd('o')
            commands.buffer('1')
        """
        super().setUp()
        self.run_setup()

    def tearDown(self):
        """Per test clean up."""

    @test(testID='dispbuf-create')
    def create_display_buffer(self):
        """Create a display-only buffer.

        The modifiable context manager is used when changes need to be made.

        :<py>:
            buf = vpe.get_display_buffer('test')
            buf.show()
            with buf.modifiable():
                buf[:] = ['One', 'Two']
            res = Struct()
            res.cur_buf = vim.current.buffer.name
            res.lines = list(vim.current.buffer)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('/[[test]]', fix_path(res.cur_buf))
        failUnlessEqual(['One', 'Two'], res.lines)

    @test(testID='dispbuf-split-show')
    def show_display_buffer_in_split(self):
        """A display buffer can be shown in the upper part of a split window.

        The number of lines left in the lower window is specified using the
        splitlines argument.

        :<py>:
            res = Struct()
            buf = vpe.get_display_buffer('test')
            win = vim.current.window
            res.orig_lines = win.height
            buf.show(splitlines=3)
            win = vim.current.window
            res.top_lines = win.height
            res.bottom_lines = vim.windows[win.number].height
            with buf.modifiable():
                buf[:] = ['One', 'Two']
            res.cur_buf = vim.current.buffer.name
            res.lines = list(vim.current.buffer)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('/[[test]]', fix_path(res.cur_buf))
        failUnlessEqual(['One', 'Two'], res.lines)
        failUnlessEqual(3, res.bottom_lines)
        failUnlessEqual(res.orig_lines, res.top_lines + 4)

    @test(testID='dispbuf-split-show-set-display')
    def show_split_set_disp_buf_size(self):
        """A split can specify the number of lines for the display buffer.

        The number of lines is specified using a negative value for the
        splitlines argument.

        :<py>:
            res = Struct()
            buf = vpe.get_display_buffer('test')
            win = vim.current.window
            res.orig_lines = win.height
            buf.show(splitlines=-3)
            win = vim.current.window
            res.top_lines = win.height
            res.bottom_lines = vim.windows[win.number].height
            with buf.modifiable():
                buf[:] = ['One', 'Two']
            res.cur_buf = vim.current.buffer.name
            res.lines = list(vim.current.buffer)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('/[[test]]', fix_path(res.cur_buf))
        failUnlessEqual(['One', 'Two'], res.lines)
        failUnlessEqual(3, res.top_lines)
        failUnlessEqual(res.orig_lines, res.bottom_lines + 4)

    @test(testID='dispbuf-split-squeeze-lower')
    def lower_window_is_made_smaller(self):
        """The display buffer will be given a minimum of one line.

        If necessary the upper window is given fewer lines than requested.
        :<py>:
            res = Struct()
            buf = vpe.get_display_buffer('test')
            win = vim.current.window
            res.orig_lines = win.height
            res.ok = buf.show(splitlines=res.orig_lines - 1)
            win = vim.current.window
            res.top_lines = win.height
            res.bottom_lines = vim.windows[win.number].height
            with buf.modifiable():
                buf[:] = ['One', 'Two']
            res.cur_buf = vim.current.buffer.name
            res.lines = list(vim.current.buffer)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('/[[test]]', fix_path(res.cur_buf))
        failUnlessEqual(['One', 'Two'], res.lines)
        failUnlessEqual(res.orig_lines - 2, res.bottom_lines)
        failUnlessEqual(1, res.top_lines)
        failUnless(res.ok)

    @test(testID='dispbuf-vsplit-show')
    def show_display_buffer_in_vsplit(self):
        """A display buffer can be shown in the left part of a split window.

        The number of columns left in the right window is specified using the
        splitcols argument.

        :<py>:
            res = Struct()
            buf = vpe.get_display_buffer('test')
            win = vim.current.window
            res.orig_cols = win.width
            buf.show(splitcols=3)
            win = vim.current.window
            res.top_cols = win.width
            res.bottom_cols = vim.windows[win.number].width
            with buf.modifiable():
                buf[:] = ['One', 'Two']
            res.cur_buf = vim.current.buffer.name
            res.lines = list(vim.current.buffer)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('/[[test]]', fix_path(res.cur_buf))
        failUnlessEqual(['One', 'Two'], res.lines)
        failUnlessEqual(3, res.bottom_cols)
        failUnlessEqual(res.orig_cols, res.top_cols + 4)

    @test(testID='dispbuf-vsplit-show-set-display')
    def show_vsplit_set_disp_buf_size(self):
        """A split can specify the number of lines for the display buffer.

        The number of lines is specified using a negative value for the
        splitcols argument.

        :<py>:
            res = Struct()
            buf = vpe.get_display_buffer('test')
            win = vim.current.window
            res.orig_cols = win.width
            buf.show(splitcols=-3)
            win = vim.current.window
            res.top_cols = win.width
            res.bottom_cols = vim.windows[win.number].width
            with buf.modifiable():
                buf[:] = ['One', 'Two']
            res.cur_buf = vim.current.buffer.name
            res.lines = list(vim.current.buffer)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('/[[test]]', fix_path(res.cur_buf))
        failUnlessEqual(['One', 'Two'], res.lines)
        failUnlessEqual(3, res.top_cols)
        failUnlessEqual(res.orig_cols, res.bottom_cols + 4)

    @test(testID='dispbuf-split-fails')
    def split_fails(self):
        """Split and show will fail if the window is too short.

        Basically, it must be at least 3 lines.
        :<py>:
            res = Struct()
            buf = vpe.get_display_buffer('test')
            commands.wincmd('s')
            win = vim.current.window
            win.height = 2
            res.ok = buf.show(splitlines=1)
            dump(res)
        """
        res = self.run_self()
        failIf(res.ok)
        failIfEqual('/[[test]]', res.cur_buf)

    @test(testID='dispbuf-vsplit-fails')
    def vsplit_fails(self):
        """Split and show will fail if the window is too narrow.

        Basically, it must be at least 3 columns.
        :<py>:
            res = Struct()
            buf = vpe.get_display_buffer('test')
            commands.wincmd('v')
            win = vim.current.window
            win.width = 2
            res.ok = buf.show(splitcols=1)
            dump(res)
        """
        res = self.run_self()
        failIf(res.ok)
        failIfEqual('/[[test]]', res.cur_buf)

    @test(testID='dispbuf-get')
    def get_twice(self):
        """The get_display_buffer function returns the same buffer.

        Given the same name, get_display_buffer returns the same buffer
        instance.

        :<py>:
            res = Struct()

            buf = vpe.get_display_buffer('test')
            buf_b = vpe.get_display_buffer('test-b')
            res.different = buf is not buf_b

            buf_again = vpe.get_display_buffer('test')
            res.same = buf_again is buf

            dump(res)
        """
        res = self.run_self()
        failUnless(res.different)
        failUnless(res.same)

    @test(testID='dispbuf-wrap')
    def wrap_existing(self):
        """The get_display_buffer function will wrap an existing buffer.

        If a buffer with a matching name already exists, it gets wrapped
        as a display buffer.

        :<py>:
            import platform
            res = Struct()

            name = 'existing'
            if platform.system() == 'Windows':
                disp_name = rf'C:\[[{name}]]'
            else:
                disp_name = f'/[[{name}]]'
            commands.new()
            b = vim.current.buffer
            res.orig_num = b.number
            b.name = disp_name

            buf = vpe.get_display_buffer(name)
            res.wrapped_num = buf.number

            dump(res)
        """
        res = self.run_self()
        failUnless(res.wrapped_num is not None)
        failUnlessEqual(res.orig_num, res.wrapped_num)

    @test(testID='dispbuf-ext-name')
    def display_buffer_ext_name(self):
        """A Scratch buffer's name may an extension part.

        The extension can be changed.

        :<py>:

            res = Struct()
            buf = vpe.get_display_buffer('test')
            res.simple_name = buf.name
            buf.set_ext_name('aaa')
            res.ext_aaa_name = buf.name
            buf.set_ext_name('bbb')
            res.ext_bbb_name = buf.name
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('/[[test]]', fix_path(res.simple_name))
        failUnlessEqual('/[[test]]/aaa', fix_path(res.ext_aaa_name))
        failUnlessEqual('/[[test]]/bbb', fix_path(res.ext_bbb_name))

    @test(testID='dispbuf-syntax-prefix')
    def syntax_prefix(self):
        """The syntax_prefix property is helps uniquely name syntax groups.

        :<py>:

            res = Struct()
            buf = vpe.get_display_buffer('test')
            res.syn_prefix = buf.syntax_prefix
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('Syn_test_', res.syn_prefix)


class Timers(support.Base):
    """Timers.

    The Timer class provides a clean interface to using Vim's timer functions.
    """
    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:
            import time
        """
        super().suiteSetUp()
        self.run_suite_setup()

    @classmethod
    def extract_from_lines(
            cls, lines: list[str], pattern: str, after: str = '') -> str:
        """Extract a line from a list of lines, using a search pattern."""
        if after:
            for line in lines:
                if line == after:
                    break
            else:
                return ''

        for line in lines:
            if re.search(pattern, line):
                return line
        return ''

    @classmethod
    def extract_log_line(
            cls, lines: list[str], pattern: str) -> str:
        """Extract a line from a list of log lines, using a search pattern."""

        line = cls.extract_from_lines(lines, pattern)
        m = re.match('^ *[0-9]+[.][0-9]{2}: (.*)', line)
        if m:
            line = m.group(1)
        else:
            line = line[9:]
        return line.rstrip()

    def do_continue(self):
        """Contine executions to allow timers to expire.

        :<py>:
            res.paused = timer.paused
            res.dead = timer.dead
            res.fire_count = timer.fire_count
            res.repeat = timer.repeat
            res.wibble = 'Wibble!'
            res.curr_time = time.time()
            dump(res)
        """
        return self.run_continue()

    def do_continue_for_time_estimation(self):
        """A verions of `do_continue` just for execution time estimation.

        :<py>:
            res = Struct()
            res.paused = 42
            res.dead = 43
            res.fire_count = 44
            res.repeat = 45
            res.wibble = 'Wibble!'
            res.curr_time = time.time()
            dump(res)
        """
        return self.run_continue()

    def do_dead_continue(self):
        """Contine executions to allow dead/unreachable timers to expire.

        :<py>:
            print("CONT", res.ticks)
            dump(res)
        """
        return self.run_continue()

    def do_dead_continue_get_log(self):
        """Contine executions to allow dead/unreachable timers to expire.

        :<py>:
            res.log = vpe.log.lines
            dump(res)
        """
        return self.run_continue()

    @test(testID='timer-one-shot')
    def create_one_shot(self):
        """Create a simple one-shot timer using.

        :<py>:
            def on_expire(timer):
                res.ticks += 1

            res = Struct()
            res.start_time = time.time()
            timer = vpe.Timer(ms=10, func=on_expire)
            res.init_time = timer.time
            res.ticks = 0
            res.repr = repr(timer)
            res.init_repeat = timer.repeat
            dump(res)
        """
        res = self.run_self()
        a = time.time()
        count = 0
        while time.time() - a < 1.0 and res.ticks < 1:
            res = self.do_continue()
            count += 1
        failUnlessEqual(1, res.ticks)
        failUnless(count > 0)
        failUnlessEqual(10, res.init_time)
        failUnless(res.dead)
        failUnlessEqual(1, res.fire_count)
        failUnlessEqual('<Timer:on_expire>', res.repr)

    @test(testID='timer-repeat')
    def create_repeating(self):
        """Create a simple repeating timer using.

        :<py>:
            def on_expire(timer):
                res.ticks += 1
                res.repeats.append(timer.repeat)
                res.rems.append(timer.remaining)
                res.paused = timer.paused

            res = Struct()
            res.start_time = time.time()
            timer = vpe.Timer(ms=1, func=on_expire, repeat=3)
            res.ticks = 0
            res.repeats = []
            res.rems = []
            res.paused = True
            dump(res)
        """
        res = self.run_self()
        a = time.time()
        count = 0
        while time.time() - a < 1.0 and res.ticks < 3:
            res = self.do_continue()
            count += 1
        failUnlessEqual(3, res.ticks)
        failUnless(count >= 1)
        failUnlessEqual([2, 1, 0], res.repeats)
        failUnless(max(res.rems) <= 100)
        failIf(res.paused)

    def resume_timer(self):
       """Resume execution of the test timer.

        :<py>:
            timer.resume()
            res.paused = timer.paused
            dump(res)
       """
       return self.run_self()

    # TODO: Vim timers seem to behave badly and unpredictably if the remaining
    #       time hits zero whilst paused.
    #       So I had this test using a 1000ms timer, with the comment:
    #          This is why the interval in this test is 100ms. Too small a
    #          number and the test is unrealiable (at least on Windows).
    @test(testID='timer-control')
    def control_timer(self):
        """The pause, resume and stop functions control an active timer.

        :<py>:

            def on_expire(timer):
                res.ticks += 1
                if res.ticks == 1:
                    timer.pause()
                elif res.ticks == 2:
                    timer.stop()
                res.paused = timer.paused

            res = Struct()
            res.start_time = time.time()
            timer = vpe.Timer(ms={interval_ms}, func=on_expire, repeat=3)
            res.ticks = 0
            dump(res)
        """
        # Make a measurement of how long it takes to execute code in the Vim
        # session and use it to choosea suitable interval. (We want the
        # do_continue to be able to execute 5 plus times within the interval.)
        a = time.time()
        res = self.do_continue_for_time_estimation()
        b = time.time()
        interval_ms = int((b - a) * 6000)
        interval = interval_ms / 2.0

        res = self.run_self(interval_ms=interval_ms)
        a = time.time()
        while time.time() - a < interval and res.ticks < 1:
            b = time.time()
            res = self.do_continue()
        b = time.time()
        failUnless(res.paused)

        res = self.resume_timer()
        failIf(res.paused)

        while time.time() - a < interval * 3 and res.ticks < 2:
            res = self.do_continue()
        failUnlessEqual(2, res.ticks)

    @test(testID='call-soon')
    def call_soon(self):
        """The call_soon function.

        This arranges to invoke a function as soon as possible, but within
        Vim's mainloop code (i.e. not within cany callback context).

        :<py>:

            def on_expire():
                print("EXPIRE")
                res.ticks += 1

            res = Struct()
            res.start_time = time.time()
            res.ticks = 0
            vpe.call_soon(on_expire)
            vpe.call_soon(on_expire)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(0, res.ticks)
        res = self.do_dead_continue()
        res = self.do_dead_continue()
        res = self.do_dead_continue()
        failUnlessEqual(2, res.ticks)

    @test(testID='call-soon-once')
    def call_soon_once(self):
        """The call_soon_once function.

        Like call_soon, but only a single call is made for a given token.

        :<py>:

            def on_expire():
                res.ticks += 1

            res = Struct()
            res.start_time = time.time()
            res.ticks = 0
            vpe.call_soon_once(vpe, on_expire)
            vpe.call_soon_once(vpe, on_expire)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(0, res.ticks)
        res = self.do_dead_continue()
        failUnlessEqual(1, res.ticks)

    @test(testID='call-soon-error')
    def call_soon_error(self):
        """Errors for call_soon invocations are logged but otherwises
        suppressed.

        :<py>:

            def on_expire():
                assert False

            res = Struct()
            res.start_time = time.time()
            res.ticks = 0
            vpe.log.clear()
            vpe.call_soon(on_expire)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(0, res.ticks)
        res = self.do_dead_continue_get_log()
        failUnlessEqual(0, res.ticks)
        failUnlessEqual(
            'VPE: Exception occurred in callback.',
            self.extract_log_line(res.log, 'callback'))

    @test(testID='timer-dead-func-single_shot')
    def dead_callback_single_shot(self):
        """A single shot timer keeps hard reference to a function and timer.

        This means the user does not need to keep a reference to the function
        or timer instance. The VPE code cleans up the Timer instance once the
        timer has expired.

        :<py>:
            def on_expire(timer):
                res.ticks += 1

            res = Struct()
            res.start_time = time.time()
            vpe.OneShotTimer(ms=10, func=on_expire)
            del on_expire
            res.ticks = 0
            dump(res)
        """
        res = self.run_self()
        a = time.time()
        while time.time() - a < 1.0 and res.ticks < 1:
            res = self.do_dead_continue()
        failUnlessEqual(1, res.ticks)

    @test(testID='timer-dead-method-single_shot')
    def dead_method_single_shot(self):
        """A single shot timer keeps hard reference to a function and method.

        This means the user does not need to keep a reference to the method's
        class instance.  The VPE code cleans up the Timer instance once the
        timer has expired.

        :<py>:
            class Test:
                def on_expire(self, timer):
                    res.ticks += 1

            res = Struct()
            res.start_time = time.time()
            inst = Test()
            vpe.OneShotTimer(ms=50, func=inst.on_expire)
            del inst
            res.ticks = 0
            dump(res)
        """
        res = self.run_self()
        a = time.time()
        while time.time() - a < 5.0 and res.ticks < 1:
            res = self.do_dead_continue()
        failUnlessEqual(1, res.ticks)

    @test(testID='timer-dead-func-repeating')
    def dead_callback_repeating(self):
        """A repeating timer keeps a weak reference to a function.

        This means that if the user drops the reference to the function then
        the timer becomes dead.

        :<py>:
            def on_expire(timer):
                res.ticks += 1

            res = Struct()
            res.start_time = time.time()
            timer = vpe.Timer(ms=10, func=on_expire, repeat=2)
            del on_expire
            res.dead = timer.dead
            dump(res)
        """
        res = self.run_self()
        failUnless(res.dead)

    @test(testID='timer-callback-exception')
    def timer_callback_raises_exception(self):
        """A timer callback exception is cleanly handled.

        :<py>:
            def on_expire(timer):
                res.ticks += 1
                if res.ticks == 1:
                    assert False

            res = Struct()
            res.start_time = time.time()
            timer = vpe.Timer(ms=10, func=on_expire, repeat=3)
            res.ticks = 0
            dump(res)
        """
        res = self.run_self()
        a = time.time()
        while time.time() - a < 1.0 and res.ticks < 3:
            res = self.do_continue()
        failUnlessEqual(3, res.ticks)


class Log(support.Base):
    """Logging buffer support.

    The Log class provides a way to log to a Vim buffer.
    """
    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            def clean_log_lines(lines):
                return [line.partition(': ')[2] for line in lines]
        """
        super().suiteSetUp()
        self.run_suite_setup()

    def setUp(self):
        """Called to set up each test.

        :<py>:

            from vpe import commands
            commands.wincmd('o')
        """
        super().setUp()
        self.run_setup()

    @test(testID='log-create')
    def create_log(self):
        """Create a Log instance.

        The default maximium length for a log is 500.

        This does not initially create a Vim buffer, just an internal FIFO to
        store logged output. When the `show` is invoked then the buffer is
        created and populated fom the FIFO.

        The show method will split the window if the buffer is not already
        visible on the current tab.

        :<py>:
            res = Struct()
            res.init_buf_count = len(vim.buffers)
            log = vpe.Log('test-log', timestamps=False)
            log('Just for testing')
            res.maxlen = log.maxlen
            res.log_buf_count = len(vim.buffers)

            res.init_win_count = len(vim.windows)
            log.hide()
            res.log_win_count_a = len(vim.windows)

            log.show()
            res.log_win_count_b = len(vim.windows)

            log.show()
            res.log_win_count_c = len(vim.windows)

            log.hide()
            res.log_win_count_d = len(vim.windows)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.init_buf_count, res.log_buf_count)
        failUnlessEqual(1, res.init_win_count)
        failUnlessEqual(1, res.log_win_count_a)
        failUnlessEqual(2, res.log_win_count_b)
        failUnlessEqual(2, res.log_win_count_c)
        failUnlessEqual(1, res.log_win_count_d)
        failUnlessEqual(500, res.maxlen)

    @test(testID='log-internal-buffer')
    def buffer_log(self):
        """A log buffers output until shown.

        The buffer has a configurable, limited length. This is enforced before
        and after the buffer is shown.

        Each lines is prefixed by a simple time stamp (seconds since the log
        was created).

        :<py>:

            name = 'test-log-2'
            disp_name = get_disp_name(name)
            res = Struct()
            res.init_buf_count = len(vim.buffers)
            log = vpe.Log(name, maxlen=5)
            res.init_buf =  vpe.find_buffer_by_name(disp_name)

            for i in range(7):
                log(f'L{i + 1}')
            log.show()
            res.shown_buf = vpe.find_buffer_by_name(disp_name)
            if res.shown_buf is not None:
                res.raw_lines = list(res.shown_buf)
                res.lines = clean_log_lines(res.shown_buf)

                log('L8')
                res.more_lines = clean_log_lines(res.shown_buf)

            dump(res)
        """
        res = self.run_self()
        failUnless(res.init_buf is None)
        failIf(res.shown_buf is None)
        failUnlessEqual(['L3', 'L4', 'L5', 'L6', 'L7'], res.lines)
        failUnlessEqual(['L4', 'L5', 'L6', 'L7', 'L8'], res.more_lines)
        failUnlessEqual('   0.00: L3', res.raw_lines[0])

    @test(testID='log-multi-line')
    def multiple_log_lines(self):
        r"""Multi-line logging works OK.

        Only the first line gets a time stamp.

        :<py>:

            name = 'test-log-3'
            disp_name = get_disp_name(name)
            res = Struct()
            log = vpe.Log(name, maxlen=5)

            log('L1\nL2')
            log.show()
            buf = vpe.find_buffer_by_name(disp_name)
            res.raw_lines = list(buf)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('   0.00: L1', res.raw_lines[0])
        failUnlessEqual('         L2', res.raw_lines[1])

    @test(testID='log-redirect')
    def log_redirect(self):
        r"""Stdout and stderr can be redirected to a log.

        :<py>:

            name = 'test-log'
            disp_name = get_disp_name(name)
            res = Struct()
            log = vpe.Log(name, maxlen=5)
            log.clear()
            log.redirect()
            print('L', end='')
            print('1\nL2')
            log.unredirect()
            print('The end')
            log.unredirect()

            log.show()
            buf = vpe.find_buffer_by_name(disp_name)
            res.lines = clean_log_lines(buf)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('L1', res.lines[0])
        failUnlessEqual('L2', res.lines[1])
        failUnlessEqual(2, len(res.lines))

    @test(testID='log-change-maxlen')
    def log_change_maxlen(self):
        """The maximum length (number of lines)can be changed.

        Earlied lines are removed if necessary. The Vim buffer is updated to
        refect the change.
        :<py>:

            name = 'test-log-4'
            disp_name = get_disp_name(name)
            res = Struct()
            res.init_buf_count = len(vim.buffers)
            log = vpe.Log(name, maxlen=5)
            res.init_buf =  vpe.find_buffer_by_name(disp_name)

            for i in range(7):
                log(f'L{i + 1}')
            log.show()
            buf = vpe.find_buffer_by_name(disp_name)
            res.lines = clean_log_lines(buf)

            log.set_maxlen(3)
            res.trimmed_lines = clean_log_lines(buf)
            log(f'L8')
            res.more_lines = clean_log_lines(buf)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['L3', 'L4', 'L5', 'L6', 'L7'], res.lines)
        failUnlessEqual(['L5', 'L6', 'L7'], res.trimmed_lines)
        failUnlessEqual(['L6', 'L7', 'L8'], res.more_lines)

    @test(testID='log-wipeout')
    def log_survives_buffer_wipeout(self):
        """Issue #2. The log's buffer may be wiped out without problems.

        A new buffer is created by show().

        :<py>:

            res = Struct()

            name = 'test-log-5'
            disp_name = get_disp_name(name)
            res.init_buf_count = len(vim.buffers)
            log = vpe.Log(name, maxlen=5)
            res.init_buf = vpe.find_buffer_by_name(disp_name)   # Expect None

            log('A line in the log')
            log.show()
            res.shown_buf = vpe.find_buffer_by_name(disp_name)
            if res.shown_buf is not None:
                vpe.commands.bwipeout(a=res.shown_buf.number)
                log('Another line in the log')
                res.dead_buf = vpe.find_buffer_by_name(disp_name) # Expect None
                res.log_lines = clean_log_lines(log.lines)

            log.show()
            res.new_shown_buf = vpe.find_buffer_by_name(disp_name)
            res.new_log_lines = clean_log_lines(res.new_shown_buf)

            dump(res)
        """
        res = self.run_self()
        failUnless(res.init_buf is None)
        failUnless(res.dead_buf is None)
        failIf(res.shown_buf is None)
        failIf(res.new_shown_buf is None)
        failIfEqual(res.new_shown_buf.number, res.shown_buf.number)
        failUnlessEqualStrings(
            literalText2Text('''
            | A line in the log
            | Another line in the log
            '''), '\n'.join(res.log_lines))
        failUnlessEqualStrings(
            literalText2Text('''
            | A line in the log
            | Another line in the log
            '''), '\n'.join(res.new_log_lines))


class AutoCmdGroup(support.CommandsBase):
    """The AutoCmdGroup context manager.

    The AutoCmdGroup class provides a way to define auto commands that invoke
    Vim functions.
    """
    # pylint: disable=invalid-name
    # pylint: disable=missing-class-docstring
    # pylint: disable=missing-function-docstring

    @test(testID='autocmd-create')
    def create_autocmds(self):
        """Create some auto commands in a group.

        :<vim>:

            set cpoptions&vim
            augroup test
            autocmd!
            autocmd BufReadPre <buffer> call VPE_Call("{uid_a}", "callback")
            autocmd BufReadPost *.py call VPE_Call("{uid_b}", "callback")
            augroup END
        """
        def callback():
            pass

        with vpe.AutoCmdGroup('test') as grp:
            grp.delete_all()
            grp.add('BufReadPre', callback)
            grp.add('BufReadPost', callback, pat='*.py')
        uid_a = utils.uid_source.prev_id(1)
        uid_b = utils.uid_source.prev_id()
        self.check_commands(uid_a=uid_a, uid_b=uid_b)

    @test(testID='autocmd-buf_as_pat')
    def create_buf_as_pat(self):
        """The pattern argument may be a Buffer instance.

        :<vim>:

            set cpoptions&vim
            augroup test
            autocmd!
            autocmd BufReadPre <buffer=1> call VPE_Call("{uid_a}", "callback")
            augroup END
        """
        def callback():
            pass

        with vpe.AutoCmdGroup('test') as grp:
            grp.delete_all()
            grp.add('BufReadPre', callback, pat=vpe.vim.current.buffer)
        uid_a = utils.uid_source.prev_id()
        self.check_commands(uid_a=uid_a)

    @test(testID='autocmd-options')
    def create_with_options(self):
        """The once and nested options are available.

        :<vim>:

            set cpoptions&vim
            augroup test
            autocmd!
            autocmd BufReadPre <buffer> ++once ++nested call VPE_Call("{uid_a}", "callback")
            augroup END
        """
        def callback():
            pass

        with vpe.AutoCmdGroup('test') as grp:
            grp.delete_all()
            grp.add('BufReadPre', callback, once=True, nested=True)
        uid_a = utils.uid_source.prev_id()
        self.check_commands(uid_a=uid_a)

    @test(testID='autocmd-event_handler')
    def create_using_event_handler_mixin(self):
        """The EventHandler mixin provides decorators for event handling.

        Invalid characters in autocmd groups are changed to 'x' 'under the
        bonnet'.

        :<vim>:

            set cpoptions&vim
            augroup testx_autocmds
            autocmd BufReadPre * call VPE_Call("{uid_a}", "EH_Test.callback")
            augroup END
        """
        class EH_Test(vpe.EventHandler):
            def __init__(self):
                self.auto_define_event_handlers('test+_autocmds')

            @vpe.EventHandler.handle('BufReadPre')
            def callback(self):
                pass

        _inst = EH_Test()
        uid_a = utils.uid_source.prev_id()
        self.check_commands(uid_a=uid_a)

    @test(testID='autocmd-event_handler-del-all')
    def create_using_event_handler_mixin_del_all(self):
        """The EventHandler mixin supports optional group deletion.

        :<vim>:

            set cpoptions&vim
            augroup testx_autocmds
            autocmd!
            autocmd BufReadPre * call VPE_Call("{uid_a}", "EH_Test.callback")
            augroup END
        """
        class EH_Test(vpe.EventHandler):
            def __init__(self):
                self.auto_define_event_handlers(
                    'test+_autocmds', delete_all=True)

            @vpe.EventHandler.handle('BufReadPre')
            def callback(self):
                pass

        _inst = EH_Test()
        uid_a = utils.uid_source.prev_id()
        self.check_commands(uid_a=uid_a)

    @test(testID='autocmd-event_handler-bad-name')
    def event_handler_mixin_bad_name(self):
        """A name that cannot be converted is handled.

        An error message is printed and no handler installed.

        :<vim>:

            <NOP>
        """
        class EH_Test(vpe.EventHandler):
            def __init__(self):
                self.auto_define_event_handlers('')

            @vpe.EventHandler.handle('BufReadPre')
            def callback(self):
                pass

        _inst = EH_Test()
        self.check_commands()


class Miscellaneous(support.CommandsBase):
    """Some miscellaneous extensions.

    Things that do not really need their own suite.
    """
    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            from vpe import commands
        """
        super().suiteSetUp()
        self.run_suite_setup()

    def setUp(self):
        """Per test set up.

        :<py>:

            commands.wincmd('o')
            commands.buffer('1')
        """
        super().setUp()
        self.run_setup()

    def do_continue(self):
        """Contine executions to allow things to flush.

        :<py>:

            res.messages = vim.execute('messages')
            dump(res)
        """
        return self.run_continue()

    @test(testID='misc-highlight')
    def highlight(self):
        """The highlight function for generating highlight commands.

        :<vim>:

            keepalt highlight clear
            keepalt highlight clear test
            keepalt highlight test NONE
            keepalt highlight test default guifg='Blue' guibg='DodgerBlue3'
            keepalt highlight test gui='bold' ctermfg=17
            keepalt highlight link PythonFunction Function
        """
        vpe.highlight(clear=True)
        vpe.highlight(group='test', clear=True)
        vpe.highlight(group='test', disable=True)
        vpe.highlight(
            group='test', default=True, guifg='Blue', guibg='DodgerBlue3')
        vpe.highlight(group='test', gui='bold', ctermfg='NavyBlue')
        vpe.highlight(group='PythonFunction', link='Function')
        self.check_commands()

    @test(testID='misc-callback')
    def callback_invocation(self):
        """Invocation of callback functions.

        :<py>:

            def my_callback(*args):
                res.args = args

            res = Struct()
            cb = vpe.Callback(my_callback, vim_exprs=(
                vpe.expr_arg('[1, 2]'), vpe.expr_arg('{"a": 1, "b": 2}'),
                'hello'))
            res.ret = vim.eval(cb.as_invocation())
            res.repr = repr(cb)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(([1, 2], {'a': 1, 'b': 2}, 'hello'), res.args)
        failUnlessEqual('<Callback:my_callback>', res.repr)

    @test(testID='misc-callback_failure')
    def callback_failure_handling(self):
        """Callback failures are elegantly handled.

        :<py>:

            class BadClass:
                def fail(self):
                    res.method_invoked = True
                    res.method_count = 1
                    assert False
                    res.method_count += 1


            def callback_fail():
                res.invoked = True
                res.count = 1
                assert False
                res.count += 1


            def callback_deleted():
                res.impossible = True


            res = Struct()
            inst = BadClass()
            cb_fail = vpe.Callback(callback_fail)
            cb_method_fail = vpe.Callback(inst.fail)
            cb_deleted = vpe.Callback(callback_deleted)
            del callback_deleted

            vim.command(cb_fail.as_call())
            vim.command(cb_method_fail.as_call())
            vim.command(cb_deleted.as_call())

            res.repr_deleted = repr(cb_deleted)
            res.repr_method = repr(cb_method_fail)

            dump(res)
        """
        res = self.run_self()
        failUnless(res.invoked)
        failUnless(res.method_invoked)
        failUnlessEqual(1, res.count)
        failUnlessEqual(1, res.method_count)
        failIf(res.impossible)

        failUnlessEqual('<Callback:callback_deleted dead!>', res.repr_deleted)
        failUnlessEqual('<Callback:BadClass.fail>', res.repr_method)

    @test(testID='misc-build-dict-arg')
    def build_dict_arg(self):
        """The build_dict_arg function converts keyword args to a dictionary.

        This is useful for translating from keyword args to pass as a dict to a
        Vim function. The arguments with values of None are omitted from the
        generated dict.
        """
        failUnlessEqual(
            {'a': 1, 'c': 'hi'},
            vpe.build_dict_arg(('a', 1), ('b', None), ('c', 'hi')))

    @test(testID='misc-error-msg')
    def error_msg(self):
        """The error_msg function writes a message in error colors.

        Unlike using 'vim.echoerr' this does not raise a vim.error.
        :<py>:

            vim.command('messages clear')
        """
        self.run_self()
        _v = self.vs.py_eval('vpe.error_msg("Oops!")')
        messages = self.vs.execute_vim_command('messages').splitlines()
        failUnlessEqual('Oops!', messages[-1])

    @test(testID='misc-error-msg-soon')
    def error_msg_soon(self):
        """The error_msg soon argument delays execution until 'safe'.

        The actual call is invoked when Vim becomes idle.

        TODO: This is currently only driving coverage. It does not prove when
              the message code is run.
        :<py>:

            vim.command('messages clear')
        """
        self.run_self()
        _v = self.vs.py_eval('vpe.error_msg("Oops!", soon=True)')
        messages = self.vs.execute_vim_command('messages').splitlines()
        failUnlessEqual('Oops!', messages[-1])

    @test(testID='misc-warning-msg')
    def warning_msg(self):
        """The warning_msg function writes a message in warning colors.

        :<py>:

            vim.command('messages clear')
        """
        self.run_self()
        _v = self.vs.py_eval('vpe.warning_msg("Careful!")')
        messages = self.vs.execute_vim_command('messages').splitlines()
        failUnlessEqual('Careful!', messages[-1])

    @test(testID='misc-echo-msg')
    def echo_msg(self):
        """The echo_msg function writes a message that gets stored.

        :<py>:

            vim.command('messages clear')
        """
        self.run_self()
        _v = self.vs.py_eval('vpe.echo_msg("Hello")')
        messages = self.vs.execute_vim_command('messages').splitlines()
        failUnlessEqual('Hello', messages[-1])

    @test(testID='misc-pedit')
    def pedit(self):
        """The pedit function edits a file in the preview window.

        :<py>:

            res = Struct()
            vpe.pedit('/tmp/wibble')
            vpe.commands.wincmd('w')
            res.preview = vim.current.window.options.previewwindow
            vpe.pedit('/tmp/unknown', noerrors=True)
            res.name = vim.current.buffer.name
            dump(res)
        """
        res = self.run_self()
        failUnless(res.preview)
        failUnless('/tmp/unknown', res.name)

    @test(testID='misc-status')
    def log_status(self):
        """The core.log_status function provides diagnostic information.

        :<py>:

            res = Struct()
            vpe.log.clear()
            vpe.core.log_status()
            res.lines = list(vpe.log.fifo)
            dump(res)
        """
        res = self.run_self()

        # Perform a sanity check on the output.
        text = '\n'.join(res.lines)
        failUnless('Popup._popups =' in  text)
        failUnless('Callback.callbacks =' in  text)

    @test(testID='misc-add-dot-dir')
    def dot_vim_dir(self):
        """The dot_vim_dir function returns ~/.vim or its equivalent.

        :<py>:

            res = Struct()
            res.dirname = vpe.dot_vim_dir()
            res.home = os.environ['HOME']
            dump(res)
        """
        res = self.run_self()

        vimrc_path = Path('~/.vimrc').expanduser()
        vim_dir_path = Path('~/.vim').expanduser()
        if not (vimrc_path.exists() or vim_dir_path.exists()):
            xdg_vim_dir_path = Path('~/.config/vim').expanduser()
            if xdg_vim_dir_path.exists():
                vim_dir_path = xdg_vim_dir_path

        if platform.platform().startswith('CYGWIN'):
            failUnlessEqual(f'{res.home}/vimfiles', res.dirname)
        else:
            failUnlessEqual(str(vim_dir_path), res.dirname)


class DefineCommand(support.Base):
    """User defined commands.

    Things that do not really need their own suite.
    """
    def suiteSetUp(self):
        """Per test set up.

        :<py>:

            def do_command(info, *args, **kwargs):
                res.info = info
                res.args = args
                res.kwargs = kwargs

            def do_simple_command(*args, **kwargs):
                res.info = ''
                res.args = args
                res.kwargs = kwargs
        """
        super().suiteSetUp()
        self.run_suite_setup()

    # TODO: I have added 'silent!' to a number of invocations of 'TestCommand'.
    #       This is because, when running on Linux, the <mods> always has
    #       'silent!' set. Investigate why this happens.
    @test(testID='ucmd-basic')
    def basic_command(self):
        """A user defined command maps to a Python function.

        :<py>:

            res = Struct()
            vpe.define_command('TestCommand', do_command)
            vim.vim().command('silent! TestCommand')
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((), res.args)
        failUnlessEqual({}, res.kwargs)
        failUnlessEqual(1, res.info.line1)
        failUnlessEqual(1, res.info.line2)
        if vim_if.VimSession.has_patch("patch-8.0.1089"):
            failUnlessEqual(0, res.info.range)
        else:
            failUnlessEqual(-1, res.info.range)
        failUnlessEqual(-1, res.info.count)
        failUnless(res.info.bang is False)
        failUnlessEqual('silent!', res.info.mods)
        failUnlessEqual('', res.info.reg)

    @test(testID='ucmd-single-arg')
    def single_arg_command(self):
        """A user defined command  can take a single argument.

        :<py>:

            res = Struct()
            vpe.define_command('TestCommand', do_command, nargs=1)
            vim.vim().command('silent! TestCommand 1')
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(('1',), res.args)
        failUnlessEqual({}, res.kwargs)
        failUnlessEqual(1, res.info.line1)
        failUnlessEqual(1, res.info.line2)
        if vim_if.VimSession.has_patch("patch-8.0.1089"):
            failUnlessEqual(0, res.info.range)
        else:
            failUnlessEqual(-1, res.info.range)
        failUnlessEqual(-1, res.info.count)
        failUnless(res.info.bang is False)
        failUnlessEqual('silent!', res.info.mods)
        failUnlessEqual('', res.info.reg)

    @test(testID='ucmd-completion')
    def command_completion(self):
        """A user defined command can have completion specified.

        :<py>:

            res = Struct()
            vpe.define_command(
                'TestCommand', do_command, nargs='*', complete='file')
            res.captured = vim.execute('command TestCommand').splitlines()[2]
            dump(res)
        """
        res = self.run_self()
        failUnless(' file ' in res.captured)

    @test(testID='ucmd-bool-options')
    def command_bool_options(self):
        """A user defined command can support bang and bar

        :<py>:

            res = Struct()
            vpe.define_command(
                'TestCommand', do_command, nargs=1, bang=True, bar=True)
            res.captured = vim.execute('command TestCommand').splitlines()[2]
            dump(res)
        """
        res = self.run_self()
        if vim_if.VimSession.has_patch("patch-8.1.1204"):
            failUnlessEqual('!|', res.captured[:2])
        else:
            failUnlessEqual('! ', res.captured[:2])

    @test(testID='ucmd-buffer')
    def command_buffer(self):
        """A user defined command can be buffer specific.

        :<py>:

            res = Struct()
            vpe.define_command(
                'TestBufCommand', do_command, buffer=True)
            res.captured = vim.execute('command TestBufCommand').splitlines()[2]
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('b', res.captured[:4].strip())

    @test(testID='ucmd-register')
    def command_taking_reg_arg(self):
        """A user defined command can take register argument.

        :<py>:

            res = Struct()
            vpe.define_command(
                'TestCommand', do_command, register=True, nargs='*')
            vim.vim().command('silent! TestCommand c 1 2')
            res.info1 = res.info
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(('1', '2'), res.args)
        failUnlessEqual({}, res.kwargs)
        failUnlessEqual(1, res.info.line1)
        failUnlessEqual(1, res.info.line2)
        if vim_if.VimSession.has_patch("patch-8.0.1089"):
            failUnlessEqual(0, res.info.range)
        else:
            failUnlessEqual(-1, res.info.range)
        failUnlessEqual(-1, res.info.count)
        failUnless(res.info.bang is False)
        failUnlessEqual('silent!', res.info.mods)
        failUnlessEqual('c', res.info.reg)

    @test(testID='ucmd-range')
    def command_taking_range(self):
        """A user defined command can take an optional range.

        :<py>:

            res = Struct()
            vpe.define_command('TestCommand', do_command, range='%')
            vim.current.buffer[:] = [str(i) for i in range(20)]
            vim.vim().command('5,9 TestCommand')
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((), res.args)
        failUnlessEqual({}, res.kwargs)
        failUnlessEqual(5, res.info.line1)
        failUnlessEqual(9, res.info.line2)
        if vim_if.VimSession.has_patch("patch-8.0.1089"):
            failUnlessEqual(2, res.info.range)
        else:
            failUnlessEqual(-1, res.info.range)
        failUnlessEqual(9, res.info.count)
        failUnless(res.info.bang is False)
        # TODO: See earlier TODO about <mods>.
        # failUnlessEqual('silent!', res.info.mods)
        failUnlessEqual('', res.info.reg)

    @test(testID='ucmd-count')
    def command_taking_count(self):
        """A user defined command can take an optional count, with meaning.

        :<py>:

            res = Struct()
            vpe.define_command(
                'TestCommand', do_command, count=3, addr='buffers')
            vim.current.buffer[:] = [str(i) for i in range(20)]
            vim.vim().command('silent! TestCommand')
            res.captured = vim.execute('command TestCommand').splitlines()[2]
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((), res.args)
        failUnlessEqual({}, res.kwargs)
        failUnlessEqual(1, res.info.line1)
        failUnlessEqual(1, res.info.line2)
        if vim_if.VimSession.has_patch("patch-8.0.1089"):
            failUnlessEqual(0, res.info.range)
        else:
            failUnlessEqual(-1, res.info.range)
        failUnlessEqual(3, res.info.count)
        failUnless(res.info.bang is False)
        failUnlessEqual('silent!', res.info.mods)
        failUnlessEqual('', res.info.reg)
        failUnless('buf' in res.captured)

    @test(testID='ucmd-no-info')
    def command_taking_no_info(self):
        """A user defined command function can receive no info argument.

        :<py>:

            res = Struct()
            vpe.define_command(
                'TestCommand2', do_simple_command, pass_info=False)
            vim.vim().command('silent! TestCommand2')
            vim.execute('command TestCommand2').splitlines()[2]
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((), res.args)
        failUnlessEqual({}, res.kwargs)
        failUnlessEqual("", res.info)

    @test(testID='ucmd-command-handler')
    def basic_command_using_commmand_handler(self):
        """The CommandHandler provides a method decoration approach,

        The default behaviour is not to pass the information object.

        :<py>:

            res = Struct()
            class CE_Test(vpe.CommandHandler):
                def __init__(self):
                    self.auto_define_commands()

                @vpe.CommandHandler.command(
                    'TestCommand', kwargs={'extra': 'dec'})
                def handle_command(self, *args, **kwargs):
                    res.args = args
                    res.kwargs = kwargs

            inst = CE_Test()
            vim.vim().command('silent! TestCommand')
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((), res.args)
        failUnlessEqual({'extra': 'dec'}, res.kwargs)

    @test(testID='ucmd-command-handler-info')
    def commmand_handler_with_info(self):
        """The CommandHandler can decorator can specify info to be provided.

        :<py>:

            res = Struct()
            class CE_Test(vpe.CommandHandler):
                def __init__(self):
                    self.auto_define_commands()

                @vpe.CommandHandler.command(
                    'TestCommand', kwargs={'extra': 'dec'}, pass_info=True)
                def handle_command(self, info, *args, **kwargs):
                    res.info = info
                    res.args = args
                    res.kwargs = kwargs

            inst = CE_Test()
            vim.vim().command('silent! TestCommand')
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((), res.args)
        failUnlessEqual({'extra': 'dec'}, res.kwargs)
        failUnlessEqual(1, res.info.line1)
        failUnlessEqual(1, res.info.line2)
        if vim_if.VimSession.has_patch("patch-8.0.1089"):
            failUnlessEqual(0, res.info.range)
        else:
            failUnlessEqual(-1, res.info.range)
        failUnlessEqual(-1, res.info.count)
        failUnless(res.info.bang is False)
        failUnlessEqual('silent!', res.info.mods)
        failUnlessEqual('', res.info.reg)


if __name__ == '__main__':
    runModule()
