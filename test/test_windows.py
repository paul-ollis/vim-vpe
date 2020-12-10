"""Special handling of windows."""
# pylint: disable=deprecated-method

from functools import partial

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support

import vpe

_run_after = ['test_vim.py']


class WindowsList(support.Base):
    """VPE support for the windows list."""
    vim_windows: vpe.wrappers.Windows

    def suiteSetUp(self):
        """called to set up the suite."""
        super().suiteSetUp()
        self.vim_windows = self.eval('vim.windows')

    @test(testID='vim-windows')
    def vim_windows_list(self):
        """The windows list object.

        :<py>:

            res = Struct()

            windows = _vim.windows
            res.init_len = len(windows)
            vpe.commands.wincmd('s')
            res.len_two = len(windows)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.init_len)
        failUnlessEqual(2, res.len_two)


class Windows(support.Base):
    """VPE support for standard windows.

    VPE provides the `Window` class that wraps a :vim:`python-window`. The
    Window may be used in the same manner as :vim:`python-window`, but has some
    enhancements.
    """
    window: vpe.wrappers.Window

    def suiteSetUp(self):
        """called to set up the suite.
        :<py>:

            vpe.commands.wincmd('o')
        """
        super().suiteSetUp()
        self.run_self()
        self.window = self.eval('vim.current.window')

    @test(testID='win-ro-attrs')
    def read_only_attrs(self):
        """Certain Window attributes are read-only."""
        window = self.window
        attrErrorCheck = partial(failUnlessRaises, AttributeError)
        attrErrorCheck(setattr, window, 'buffer', window.buffer)
        attrErrorCheck(setattr, window, 'vars', window.vars)
        attrErrorCheck(setattr, window, 'options', window.options)
        attrErrorCheck(setattr, window, 'number', window.number)
        attrErrorCheck(setattr, window, 'row', window.row)
        attrErrorCheck(setattr, window, 'col', window.col)
        attrErrorCheck(setattr, window, 'tabpage', window.tabpage)
        attrErrorCheck(setattr, window, 'valid', window.valid)

    @test(testID='win-vars-attr')
    def window_vars_as_attributes(self):
        """Window.vars provides attribute style access.

        This is in addition to dictionary style access; making for more
        naturalistic code.

        :<py>:

            res = Struct()
            window = vim.current.window
            window.vars.temp_var = 'Hello'
            res.temp_var = _vim.bindeval('w:temp_var')
            res.alt_temp_var = window.vars.temp_var

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(b'Hello', res.temp_var)
        failUnlessEqual('Hello', res.alt_temp_var)

    @test(testID='win-options-attr')
    def window_options_as_attributes(self):
        """Window.options provides attribute style access.

        This is in addition to dictionary style access, making for more
        naturalistic code.

        :<py>:

            res = Struct()
            window = vim.current.window
            res.glob_sl = vim.options.statusline
            window.options.statusline = vim.options.statusline + 'xx'
            res.win_sl = window.options.statusline
            res.glob_sl_two = vim.options.statusline

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.glob_sl + 'xx', res.win_sl)
        failUnlessEqual(res.glob_sl, res.glob_sl_two)

    @test(testID='win-valid-flag')
    def window_valid_flag(self):
        """Window.valid attribute is set to False when a window is closed.

        :<py>:

            res = Struct()
            vpe.commands.wincmd('s')
            window = vim.current.window
            res.orig_valid = window.valid
            vpe.commands.wincmd('c')
            res.new_valid = window.valid

            dump(res)
        """
        res = self.run_self()
        failUnless(res.orig_valid)
        failIf(res.new_valid)

    @test(testID='win-goto')
    def window_goto(self):
        """Window.goto makes a window the current one.

        :<py>:

            res = Struct()
            vpe.commands.wincmd('s')
            orig_win = vim.current.window
            res.orig_win = vim.current.window.number
            vpe.commands.wincmd('w')
            res.other_win = vim.current.window.number
            orig_win.goto()
            res.final_win = vim.current.window.number

            dump(res)
        """
        res = self.run_self()
        failIfEqual(res.orig_win, res.other_win)
        failUnlessEqual(res.orig_win, res.final_win)

    @test(testID='win-close')
    def window_close(self):
        """Window.close closes the window if possible.

        :<py>:

            res = Struct()
            vpe.commands.wincmd('o')
            vpe.commands.wincmd('s')
            res.orig_n_windows = len(vim.windows)
            orig_win = vim.current.window
            vpe.commands.wincmd('w')
            res.orig_id = orig_win.id
            res.close_ok = orig_win.close()
            res.rem_n_windows = len(vim.windows)
            res.rem_id = vim.current.window.id
            res.close_fail = vim.current.window.close()

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(2, res.orig_n_windows)
        failUnlessEqual(1, res.rem_n_windows)
        failUnless(res.close_ok)
        failIf(res.close_fail)
        failIfEqual(res.orig_id, res.rem_id)

    @test(testID='win-temp-active')
    def temp_active_window(self):
        """The temp_active_window context provides controlled window switching.

        :<py>:

            res = Struct()
            vpe.commands.wincmd('s')
            orig_win = vim.current.window
            vpe.commands.wincmd('w')
            vpe.commands.edit(f'{vim.current.buffer.name}-b')
            alt_win = vim.current.window
            alt_buf = vim.current.buffer
            orig_win.goto()

            alt_buf[:] = []
            vim.current.buffer[:] = []
            with vpe.temp_active_window(alt_win):
                vim.append(0, 'Alt text')
            vim.append(0, 'Main text')
            res.main_text = vim.current.buffer[0]
            res.alt_text = alt_buf[0]

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('Alt text', res.alt_text)
        failUnlessEqual('Main text', res.main_text)

    @test(testID='win-temp-options-context')
    def temp_options_context(self):
        """The temp options context.

        The temp option values can be set using a context variables, by
        defining defaults or using the save method.

        :<py>:

            res = Struct()
            win = vim.current.window
            win.options['statusline'] = vim.options['statusline'].replace(
                'W=', 'Cols=')

            res.orig_sl = win.options['statusline']

            with win.temp_options() as opts:
                opts.statusline = res.orig_sl + 'xx'
                res.temp_sl = win.options['statusline']
            res.restored_sl = win.options['statusline']

            with win.temp_options(statusline=res.orig_sl + 'xx'):
                res.temp_sl2 = win.options['statusline']
            res.restored_sl2 = win.options['statusline']

            with win.temp_options() as opts:
                opts.save('statusline')
                win.options['statusline'] += 'xx'
                res.temp_sl3 = win.options['statusline']
            res.restored_sl3 = win.options['statusline']

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.orig_sl + 'xx', res.temp_sl)
        failUnlessEqual(res.orig_sl, res.restored_sl)
        failUnlessEqual(res.orig_sl + 'xx', res.temp_sl2)
        failUnlessEqual(res.orig_sl, res.restored_sl2)
        failUnlessEqual(res.orig_sl + 'xx', res.temp_sl3)
        failUnlessEqual(res.orig_sl, res.restored_sl3)

    @test(testID='win-save-view')
    def saved_window_view(self):
        """The saved_window_view context manager.

        This makes it easy to temporarily perform operations that make unwanted
        changes to the current window.

        :<py>:

            res = Struct()
            buf = vim.current.buffer
            buf[:] = 'One Two Three'.split()
            win = vim.current.window
            win.cursor = (1, 0)
            with vpe.saved_winview():
                win.cursor = (3, 0)
                res.context_cursor = win.cursor
            res.post_cursor = win.cursor
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((3, 0), res.context_cursor)
        failUnlessEqual((1, 0), res.post_cursor)

    @test(testID='win-vis-line-range')
    def visible_line_range(self):
        """The Window provides a visible_line_range property.

        :<py>:

            res = Struct()
            buf = vim.current.buffer
            buf[:] = [str(n) for n in range(80)]
            vpe.commands.wincmd('s')
            win = vim.current.window
            vpe.commands.resize(20)

            vim.command('1')
            res.buf_top = win.visible_line_range

            vim.command('$')
            vpe.commands.redraw()
            res.buf_bottom = win.visible_line_range

            if 'scrolloff' in win.options:
                win.options.scrolloff = 0
            else:
                vim.options.scrolloff = 0
            vpe.commands.normal('20k')
            vpe.commands.normal('5k')
            vpe.commands.normal('5k')
            vpe.commands.redraw()
            res.buf_mid = win.visible_line_range

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((0, 20), res.buf_top)
        failUnlessEqual((60, 80), res.buf_bottom)
        failUnlessEqual((49, 69), res.buf_mid)


if __name__ == '__main__':
    runModule()
