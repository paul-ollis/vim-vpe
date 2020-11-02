"""Various of the extensions in VPE."""
# pylint: disable=deprecated-method

from typing import Set, Tuple, Any
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

import vpe

_run_after = ['test_vim.py', 'test_mapping_x.py']


class TestInfo(support.Base):
    """General information features."""
    @test(testID='version')
    def version(self):
        """VPE provides a version function.

        :<py>:
            res.version = vpe.version()
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((0, 3, 0), res.version)


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
        self.run_self()

    def suiteTearDown(self):
        """Called to cleanup after the suite ends.

        :<py>:

            commands.wincmd('o')
            commands.buffer('1')
        """
        super().suiteTearDown()
        self.run_self()

    def setUp(self):
        """Per test set up.

        :<py>:

            commands.wincmd('o')
            commands.buffer('1')
        """
        super().setUp()
        self.run_self()

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
        failUnlessEqual('/[[test]]', res.cur_buf)
        failUnlessEqual(['One', 'Two'], res.lines)

    @test(testID='dispbuf-split-show')
    def show_display_buffer_in_split(self):
        """A display buffer can be shown in the upper part of a split window.

        The number of lines left in the lower buffer is specified using the
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
        failUnlessEqual('/[[test]]', res.cur_buf)
        failUnlessEqual(['One', 'Two'], res.lines)
        failUnlessEqual(3, res.bottom_lines)
        failUnlessEqual(res.orig_lines, res.top_lines + 4)

    @test(testID='dispbuf-split-squeeze-lower')
    def lower_window_is_made_smaller(self):
        """The display buffer will be given a minimum of one line.

        If necessary the lower window is given fewer lines than requested.
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
        failUnlessEqual('/[[test]]', res.cur_buf)
        failUnlessEqual(['One', 'Two'], res.lines)
        failUnlessEqual(res.orig_lines - 2, res.bottom_lines)
        failUnlessEqual(1, res.top_lines)
        failUnless(res.ok)

    @test(testID='dispbuf-split-fails')
    def split_fails(self):
        """Split and show will fail if the window iss too short.

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
            res = Struct()

            name = 'existing'
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


class Timers(support.Base):
    """Timers.

    The Timer class provides a clean interface to using Vim's timer functions.
    """
    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:
            import time

            vpe.timer_stopall()
        """
        super().suiteSetUp()
        self.run_self()

    def do_continue(self):
       """Contine executions to allow timers to expire.

        :<py>:
            res.paused = timer.paused
            res.num_timers = len(vpe.Timer._one_shot_timers)
            res.dead = timer.dead
            res.fire_count = timer.fire_count
            res.elapsed = time.time() - res.start_time
            dump(res)
       """
       return self.run_self()

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
        failUnlessEqual([3, 2, 1], res.repeats)
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

    @test(testID='timer-control')
    def control_timer(self):
        """The pause,resume and stop functions control an active timer.

        :<py>:

            def on_expire(timer):
                print(">>>", timer.fire_count)
                res.ticks += 1
                if res.ticks == 1:
                    timer.pause()
                elif res.ticks == 2:
                    timer.stop()
                res.paused = timer.paused

            res = Struct()
            res.start_time = time.time()
            timer = vpe.Timer(ms=50, func=on_expire, repeat=3)
            res.ticks = 0
            dump(res)
        """
        res = self.run_self()
        a = time.time()
        count = 0
        while time.time() - a < 0.5 and res.ticks < 1:
            res = self.do_continue()
        failUnless(res.paused)

        res = self.resume_timer()
        failIf(res.paused)

        while time.time() - a < 0.5 and res.ticks < 2:
            res = self.do_continue()
        failUnlessEqual(2, res.ticks)
        failUnlessEqual(0, res.num_timers)

    @test(testID='timer-stopall')
    def stopall_timers(self):
        """The stop_all class method stops timer and cleans up.

        :<py>:

            def on_expire(timer):
                res.ticks += 1

            res = Struct()
            res.start_time = time.time()
            timer = vpe.Timer(ms=100, func=on_expire, repeat=-1)
            timer2 = vpe.Timer(ms=100, func=on_expire)
            vpe.Timer.stop_all()
            dump(res)
        """
        self.run_self()
        res = self.do_continue()
        failUnlessEqual(0, res.num_timers)

    @test(testID='timer-call-soon')
    def call_soon(self):
        """The call_soon function.

        :<py>:

            def on_expire():
                res.ticks += 1

            res = Struct()
            res.start_time = time.time()
            res.ticks = 0
            vpe.call_soon(on_expire)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(0, res.ticks)
        res = self.do_continue()
        failUnlessEqual(1, res.ticks)
        failUnlessEqual(0, res.num_timers)

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
            vpe.Timer(ms=10, func=on_expire)
            del on_expire
            res.ticks = 0
            dump(res)
        """
        res = self.run_self()
        a = time.time()
        while time.time() - a < 1.0 and res.ticks < 1:
            res = self.do_continue()
        failUnlessEqual(1, res.ticks)
        failUnlessEqual(0, res.num_timers)

    @test(testID='timer-dead-method-single_shot')
    def dead_method_single_shot(self):
        """A single shot timer keeps hard reference to a function and method.

        This means the user does not need to keep a reference to the function
        or timer instance. The VPE code cleans up the Timer instance once the
        timer has expired.

        :<py>:
            class Test:
                def on_expire(self, timer):
                    res.ticks += 1

            res = Struct()
            res.start_time = time.time()
            inst = Test()
            vpe.Timer(ms=10, func=inst.on_expire)
            del inst
            res.ticks = 0
            dump(res)
        """
        res = self.run_self()
        a = time.time()
        while time.time() - a < 1.0 and res.ticks < 1:
            res = self.do_continue()
        failUnlessEqual(1, res.ticks)
        failUnlessEqual(0, res.num_timers)

    @test(testID='timer-dead-func-repeating')
    def dead_callback_repeating(self):
        """A single shot timer keeps weak reference to a function.

        This means that is the user drops the reference to the
        function then the timer becomes dead.

        :<py>:
            def on_expire(timer):
                res.ticks += 1

            res = Struct()
            res.start_time = time.time()
            vpe.Timer(ms=10, func=on_expire, repeat=2)
            del on_expire
            res.dead = timer.dead
            dump(res)
        """
        res = self.run_self()
        failUnless(res.dead)


class Log(support.Base):
    """Logging buffer support.

    The Log class provides a way to log to a Vim buffer.
    """
    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            def clean_log_lines(lines):
                return [line.partition(': ')[2] for line in lines]

            vpe.timer_stopall()
        """
        super().suiteSetUp()
        self.run_self()

    def setUp(self):
        """Called to set up each test.

        :<py>:

            from vpe import commands
            commands.wincmd('o')
        """
        super().setUp()
        self.run_self()

    @test(testID='log-create')
    def create_log(self):
        """Create a Log instance.

        This does not create a Vim buffer, just an internal FIFO to store
        logged output, until show is invoked.

        The show method will split the window if the buffer is not already
        visible on the current tab.

        :<py>:
            res = Struct()
            res.init_buf_count = len(vim.buffers)
            log = vpe.Log('test-log')
            res.log_buf_count = len(vim.buffers)

            res.init_win_count = len(vim.windows)
            log.show()
            res.log_win_count = len(vim.windows)

            log.show()
            res.log_win_count_b = len(vim.windows)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.init_buf_count, res.log_buf_count)
        failUnlessEqual(1, res.init_win_count)
        failUnlessEqual(2, res.log_win_count)
        failUnlessEqual(2, res.log_win_count_b)

    @test(testID='log-internal-buffer')
    def buffer_log(self):
        """A log buffers output until shown.

        The buffer has a configurable, limited length. This is enforced before
        and after the buffer is shown.

        Each lines is prefixed by a simple time stamp (seconds since log was
        created).

        :<py>:
            res = Struct()
            res.init_buf_count = len(vim.buffers)
            log = vpe.Log('test-log-2', maxlen=5)
            res.init_buf =  vpe.find_buffer_by_name('/[[test-log-2]]')

            for i in range(7):
                log(f'L{i + 1}')
            log.show()
            res.shown_buf = vpe.find_buffer_by_name('/[[test-log-2]]')
            if res.shown_buf is not None:
                res.raw_lines = list(res.shown_buf)
                res.lines = clean_log_lines(res.shown_buf)

            log(f'L8')
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

            res = Struct()
            log = vpe.Log('test-log-3', maxlen=5)

            log('L1\nL2')
            log.show()
            buf = vpe.find_buffer_by_name('/[[test-log-3]]')
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

            res = Struct()
            log = vpe.Log('test-log', maxlen=5)
            log.clear()
            log.redirect()
            print('L', end='')
            print('1\nL2')
            log.unredirect()
            print('The end')
            log.unredirect()

            log.show()
            buf = vpe.find_buffer_by_name('/[[test-log]]')
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
            res = Struct()
            res.init_buf_count = len(vim.buffers)
            log = vpe.Log('test-log-5', maxlen=5)
            res.init_buf =  vpe.find_buffer_by_name('/[[test-log-5]]')

            for i in range(7):
                log(f'L{i + 1}')
            log.show()
            buf = vpe.find_buffer_by_name('/[[test-log-5]]')
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


class AutoCmdGroup(support.CommandsBase):
    """The AutoCmdGroup context manager.

    The AutoCmdGroup class provides a way to define auto commands that invoke
    Vim functions.
    """
    @test(testID='autocmd-create')
    def create_autocmds(self):
        """Create some auto commands in a group.

        :<vim>:

            augroup test
            autocmd!
            autocmd BufReadPre <buffer> call VPE_Call("100")
            autocmd BufReadPost *.py call VPE_Call("101")
            augroup END
        """
        def callback():
            pass

        with vpe.AutoCmdGroup('test') as grp:
            grp.delete_all()
            grp.add('BufReadPre', callback)
            grp.add('BufReadPost', callback, pat='*.py')
        self.check_commands()

    @test(testID='autocmd-buf_as_pat')
    def create_buf_as_pat(self):
        """The pattern argument may be a Buffer instance.

        :<vim>:

            augroup test
            autocmd!
            autocmd BufReadPre <buffer=1> call VPE_Call("100")
            augroup END
        """
        def callback():
            pass

        with vpe.AutoCmdGroup('test') as grp:
            grp.delete_all()
            grp.add('BufReadPre', callback, pat=vpe.vim.current.buffer)
        self.check_commands()

    @test(testID='autocmd-options')
    def create_with_options(self):
        """The once and nested options are available.

        :<vim>:

            augroup test
            autocmd!
            autocmd BufReadPre <buffer> ++once ++nested call VPE_Call("100")
            augroup END
        """
        def callback():
            pass

        with vpe.AutoCmdGroup('test') as grp:
            grp.delete_all()
            grp.add('BufReadPre', callback, once=True, nested=True)
        self.check_commands()


class Miscellaneous(support.CommandsBase):
    """Some miscellaneous extensions.

    Things that do not really need their own suite.
    """
    def setUp(self):
        """Per test set up.

        :<py>:

            commands.wincmd('o')
            commands.buffer('1')
        """
        super().setUp()
        self.run_self()

    def do_continue(self):
       """Contine executions to allow things to flush.

        :<py>:

            res.messages = vim.execute('messages')
            dump(res)
       """
       return self.run_self()

    @test(testID='misc-highlight')
    def highlight(self):
        """The highlight function for generating highlight commands.

        :<vim>:

            highlight clear
            highlight clear test
            highlight test NONE
            highlight test default guifg=Blue guibg=#1874cd
            highlight test gui=bold ctermfg=16
            highlight link PythonFunction Function
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

            def callback(*args):
                res.args = args

            res = Struct()
            cb = vpe.core.Callback(callback, vim_exprs=(
                vpe.expr_arg('[1, 2]'), vpe.expr_arg('{"a": 1, "b": 2}'),
                'hello'))
            print(cb.as_invocation())
            res.ret = vim.eval(cb.as_invocation())

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(([1, 2], {'a': 1, 'b': 2}, 'hello'), res.args)

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
            cb_fail = vpe.core.Callback(callback_fail)
            cb_method_fail = vpe.core.Callback(inst.fail)
            cb_deleted = vpe.core.Callback(callback_deleted)
            del callback_deleted

            vim.command(cb_fail.as_call())
            vim.command(cb_method_fail.as_call())
            vim.command(cb_deleted.as_call())

            dump(res)
        """
        res = self.run_self()
        failUnless(res.invoked)
        failUnless(res.method_invoked)
        failUnlessEqual(1, res.count)
        failUnlessEqual(1, res.method_count)
        failIf(res.impossible)

    @test(testID='misc-build-dict-arg')
    def build_dict_arg(self):
        """The build_dict_arg function converts keyword args to a dictionary.

        This is useful for translating from keyword args to pass as a dict to a
        Vim function. The arguments with values of None are omitted from the
        generated dict.
        """
        failUnlessEqual(
            {'a': 1, 'c': 'hi'},
            vpe.core.build_dict_arg(('a', 1), ('b', None), ('c', 'hi')))

    @test(testID='misc-errmsg')
    def errmsg(self):
        """The error_msg function writes a message in error colors.

        Unlike using 'vim.echoerr' this does not raise a vim.error.
        :<py>:

            vpe.commands('messages clear')
        """
        self.run_self()
        v = self.vs.py_eval('vpe.error_msg("Oops!")')
        messages = self.vs.execute_vim('messages').splitlines()
        failUnlessEqual('Oops!', messages[-1])

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
        failUnless('Timer._one_shot_timers =' in  text)
        failUnless('Popup._popups =' in  text)
        failUnless('Callback.callbacks =' in  text)


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
        """
        super().suiteSetUp()
        self.run_self()

    @test(testID='ucmd-basic')
    def basic_command(self):
        """A user defined command maps to a Python function.

        :<py>:

            res = Struct()
            vpe.define_command('TestCommand', do_command)
            vim.vim().command('TestCommand')
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((), res.args)
        failUnlessEqual({}, res.kwargs)
        failUnlessEqual(1, res.info.line1)
        failUnlessEqual(1, res.info.line2)
        failUnlessEqual(0, res.info.range)
        failUnlessEqual(-1, res.info.count)
        failUnless(res.info.bang is False)
        failUnlessEqual('silent!', res.info.mods)
        failUnlessEqual('', res.info.reg)

    @test(testID='ucmd-single-arg')
    def single_arg_command(self):
        """A user defined command  can tage a single argument.

        :<py>:

            res = Struct()
            vpe.define_command('TestCommand', do_command, nargs=1)
            vim.vim().command('TestCommand 1')
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(('1',), res.args)
        failUnlessEqual({}, res.kwargs)
        failUnlessEqual(1, res.info.line1)
        failUnlessEqual(1, res.info.line2)
        failUnlessEqual(0, res.info.range)
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
        failUnlessEqual('!|', res.captured[:2])

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
        failUnlessEqual('b ', res.captured[:2])

    @test(testID='ucmd-register')
    def command_taking_reg_arg(self):
        """A user defined command can take register argument.

        :<py>:

            res = Struct()
            vpe.define_command(
                'TestCommand', do_command, register=True, nargs='*')
            vim.vim().command('TestCommand c 1 2')
            res.info1 = res.info
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(('1', '2'), res.args)
        failUnlessEqual({}, res.kwargs)
        failUnlessEqual(1, res.info.line1)
        failUnlessEqual(1, res.info.line2)
        failUnlessEqual(0, res.info.range)
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
        failUnlessEqual(2, res.info.range)
        failUnlessEqual(9, res.info.count)
        failUnless(res.info.bang is False)
        failUnlessEqual('silent!', res.info.mods)
        failUnlessEqual('', res.info.reg)

    @test(testID='ucmd-count')
    def command_taking_count(self):
        """A user defined command can take an optional count, with meaning.

        :<py>:

            res = Struct()
            vpe.define_command(
                'TestCommand', do_command, count=3, addr='other')
            vim.current.buffer[:] = [str(i) for i in range(20)]
            vim.vim().command('TestCommand')
            res.captured = vim.execute('command TestCommand').splitlines()[2]
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((), res.args)
        failUnlessEqual({}, res.kwargs)
        failUnlessEqual(1, res.info.line1)
        failUnlessEqual(1, res.info.line2)
        failUnlessEqual(0, res.info.range)
        failUnlessEqual(3, res.info.count)
        failUnless(res.info.bang is False)
        failUnlessEqual('silent!', res.info.mods)
        failUnlessEqual('', res.info.reg)
        failUnless('?' in res.captured)


if __name__ == '__main__':
    runModule()
