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

    @test(testID='win-temp-options-context')
    def temp_options_context(self):
        """The temp options context.

        The temp option values can be set using a context variables or by
        defining defaults.

        :<py>:

            res = Struct()
            win = vim.current.window

            res.orig_sl = win.options['statusline']
            with win.temp_options() as opts:
                opts.statusline = res.orig_sl + 'xx'
                res.temp_sl = win.options['statusline']
            res.restored_sl = win.options['statusline']

            with win.temp_options(statusline=res.orig_sl + 'xx'):
                res.temp_sl2 = win.options['statusline']
            res.restored_sl2 = win.options['statusline']

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.orig_sl + 'xx', res.temp_sl)
        failUnlessEqual(res.orig_sl, res.restored_sl)
        failUnlessEqual(res.orig_sl + 'xx', res.temp_sl2)
        failUnlessEqual(res.orig_sl, res.restored_sl2)

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


if __name__ == '__main__':
    runModule()
