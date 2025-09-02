"""Special handling of windows."""
# pylint: disable=deprecated-method
# pylint: disable=wrong-import-order
# pylint: disable=unused-wildcard-import,wildcard-import

from functools import partial

from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import Collection
from cleversheep3.Test.Tester import test, runModule

import support
import vim_if

import vpe
from vpe import windows

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

    @test(testID='vim-window-iteration')
    def vim_windows_iter(self):
        """The Vim.iter_all_windows visits windows on all tabs.

        :<py>:

            res = Struct()

            vpe.commands.tabonly()
            vpe.commands.wincmd('o')

            res.known_ids = set()
            res.known_ids.add(
                (vim.current.tabpage.number, vim.current.window.id))
            vpe.commands.wincmd('s')
            res.known_ids.add(
                (vim.current.tabpage.number, vim.current.window.id))
            vpe.commands.tabnew()
            res.known_ids.add(
                (vim.current.tabpage.number, vim.current.window.id))

            res.visited_ids = set()
            for t, w in vim.iter_all_windows():
                res.visited_ids.add((t.number, w.id))

            dump(res)
        """
        # TODO: Vim -bug: I have seem Vim segfault when this test is run.
        res = self.run_self()
        failUnlessEqual(res.visited_ids, res.known_ids)


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
            glob_status = vim.options['statusline'].replace('W=', 'Cols=')
            win.options['statusline'] = f'>>{glob_status}'

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
            vpe.commands.wincmd('o')
            vpe.commands.wincmd('s')
            win = vim.current.window
            vpe.commands.resize(20)
            vpe.commands.redraw()

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

    @test(testID='win-id-to-window')
    def window_id_to_window(self):
        """The Window for a given window-ID can be found.

        :<py>:

            res = Struct()
            vpe.commands.wincmd('o')
            vpe.commands.wincmd('s')
            win = vim.current.window
            res.n_windows = len(vim.windows)

            win_a_id = vim.win_getid(1)
            win = vpe.Window.win_id_to_window(win_a_id)
            res.win_a_number = win.number

            win_b_id = vim.win_getid(2)
            win = vpe.Window.win_id_to_window(win_b_id)
            res.win_b_number = win.number

            non_id = 1
            while non_id in (win_a_id, win_b_id):
                non_id += 1
            res_non_win = vpe.Window.win_id_to_window(non_id)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(2, res.n_windows)
        failUnlessEqual(1, res.win_a_number)
        failUnlessEqual(2, res.win_b_number)
        failUnless(res.non_win is None)


class Layout(support.Base):
    """VPE support windows layout.

    The windows.LayoutElement provides an API to work with Vim window layout.
    """
    window: vpe.wrappers.Window

    def __init__(self, *args, **kwargs):
        if not vim_if.VimSession.has_patch('patch-8.1.0307'):
            raise Collection.Unsupported
        super().__init__(*args, **kwargs)

    def setUp(self):
        """Called to set up each test.
        :<py>:

            vpe.commands.wincmd('o')
        """
        super().setUp()
        self.run_setup()

    @test(testID='layout-single')
    def single_window(self):
        """A single window yields a single LayoutWindow instance.

        The instance provides an ID and width; and has a type_name of Win.

        :<py>:

            from vpe import windows

            res = Struct()
            res.layout = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())

            dump(res)
        """
        res = self.run_self()
        failUnless(isinstance(res.layout, windows.LayoutWindow))
        failUnlessEqual('Win', res.layout.type_name)
        failUnlessEqual(100, res.layout.width)
        failUnless(isinstance(res.layout.id, int))
        failUnlessEqual(1, len(res.layout))

    @test(testID='layout-hsplit')
    def single_hsplit(self):
        """A simple horizontal split yields a LayoutColumn.

        It has a type_name of Col.
        The components LayoutWindow instances are available using indexing. In
        this scenario, the iter_windows will yield the same window instances.

        :<py>:

            from vpe import windows

            res = Struct()
            vpe.commands.split()
            res.layout = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())

            dump(res)
        """
        res = self.run_self()
        failUnless(isinstance(res.layout, windows.LayoutColumn))
        failUnlessEqual('Col', res.layout.type_name)
        failUnless(isinstance(res.layout[0], windows.LayoutWindow))
        failUnless(isinstance(res.layout[1], windows.LayoutWindow))
        for i, layout in enumerate(res.layout.iter_windows()):
            failUnless(layout is res.layout[i])
        failUnlessEqual(2, len(res.layout))

    @test(testID='layout-vsplit')
    def single_vsplit(self):
        """A simple vertical split yields a LayoutRow.

        This is analogous to the LayoutColumn. Its type_name is Col.

        :<py>:

            from vpe import windows

            res = Struct()
            vpe.commands.split(vertical=True)
            res.layout = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())

            dump(res)
        """
        res = self.run_self()
        failUnless(isinstance(res.layout, windows.LayoutRow))
        failUnlessEqual('Row', res.layout.type_name)
        failUnless(isinstance(res.layout[0], windows.LayoutWindow))
        failUnless(isinstance(res.layout[1], windows.LayoutWindow))
        for i, layout in enumerate(res.layout.iter_windows()):
            failUnless(layout is res.layout[i])
        failUnlessEqual(2, len(res.layout))

    @test(testID='layout-nested')
    def nested_splits(self):
        """Nested splits yield a nested set of rows and columns.

        The iter_windows method will yield each leaf LayoutWindow.

        For debug support, the describe method produces a clear description, as
        a sequence of lines.

        :<py>:

            from vpe import windows

            res = Struct()
            with vim.temp_options():
                vim.options.guioptions -= 'lL'
                vim.options.guioptions += 'r'
                vim.options.columns = 100

                vpe.commands.split()
                vpe.commands.split()
                vpe.commands.split(vertical=True)
                vpe.commands.split()
                res.layout = windows.LayoutElement.create_from_vim_layout(
                    vim.winlayout())

            dump(res)
        """
        res = self.run_self()
        failUnless(isinstance(res.layout, windows.LayoutColumn))
        failUnless(isinstance(res.layout[0], windows.LayoutRow))
        failUnless(isinstance(res.layout[1], windows.LayoutWindow))
        failUnless(isinstance(res.layout[2], windows.LayoutWindow))

        row = res.layout[0]
        failUnless(isinstance(row[0], windows.LayoutColumn))
        failUnless(isinstance(row[1], windows.LayoutWindow))

        col = row[0]
        failUnless(isinstance(col[0], windows.LayoutWindow))
        failUnless(isinstance(col[1], windows.LayoutWindow))

        iter_order = (
            res.layout[0][0][0],
            res.layout[0][0][1],
            res.layout[0][1],
            res.layout[1],
            res.layout[2],
        )
        for expect, win in zip(iter_order, res.layout.iter_windows()):
            failUnless(expect is win)

        lines = res.layout.describe()
        failUnlessEqual('Col = 100', lines[0])
        failUnlessEqual('    Row = 100', lines[1])
        failUnlessEqual('        Col = 50', lines[2])
        failUnlessEqual('            Win[1] = 50', lines[3])
        failUnlessEqual('            Win[2] = 50', lines[4])
        failUnlessEqual('        Win[3] = 49', lines[5])
        failUnlessEqual('    Win[4] = 100', lines[6])
        failUnlessEqual('    Win[5] = 100', lines[7])

    @test(testID='layout-adjust')
    def adjust_layout(self):
        """A layout can be adjusted to reflect a change in columns.

        It is the layout tree that is modified, the actual Vim window layout
        is only changed if apply_sizes is invoked.

        The set_widths_from_layout method allows one layout to adjust another.
        :<py>:

            from vpe import windows

            res = Struct()
            vpe.commands.split()
            vpe.commands.split()
            vpe.commands.split(vertical=True)
            vpe.commands.resize(-10, vertical=True)
            vpe.commands.split()
            res.layout = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())
            res.alt_layout = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())

            res.new_layout = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())
            vim.options.columns += 10
            vpe.commands.redraw()
            res.new_layout.adjust_width(vim.options.columns)
            res.alt_layout.set_widths_from_layout(res.new_layout)

            res.unadjusted = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())
            res.new_layout.adjust_width(vim.options.columns)

            res.new_layout.apply_sizes()
            res.adjusted = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())

            dump(res)
        """
        res = self.run_self()
        lines = res.layout.describe()
        failUnlessEqual('Col = 100', lines[0])
        failUnlessEqual('    Row = 100', lines[1])
        failUnlessEqual('        Col = 40', lines[2])
        failUnlessEqual('            Win[1] = 40', lines[3])
        failUnlessEqual('            Win[2] = 40', lines[4])
        failUnlessEqual('        Win[3] = 59', lines[5])
        failUnlessEqual('    Win[4] = 100', lines[6])
        failUnlessEqual('    Win[5] = 100', lines[7])

        lines = res.new_layout.describe()
        failUnlessEqual('Col = 110', lines[0])
        failUnlessEqual('    Row = 110', lines[1])
        failUnlessEqual('        Col = 44', lines[2])
        failUnlessEqual('            Win[1] = 44', lines[3])
        failUnlessEqual('            Win[2] = 44', lines[4])
        failUnlessEqual('        Win[3] = 65', lines[5])
        failUnlessEqual('    Win[4] = 110', lines[6])
        failUnlessEqual('    Win[5] = 110', lines[7])

        lines = res.alt_layout.describe()
        failUnlessEqual('Col = 110', lines[0])
        failUnlessEqual('    Row = 110', lines[1])
        failUnlessEqual('        Col = 44', lines[2])
        failUnlessEqual('            Win[1] = 44', lines[3])
        failUnlessEqual('            Win[2] = 44', lines[4])
        failUnlessEqual('        Win[3] = 65', lines[5])
        failUnlessEqual('    Win[4] = 110', lines[6])
        failUnlessEqual('    Win[5] = 110', lines[7])

        lines = res.unadjusted.describe()
        failUnlessEqual('Col = 110', lines[0])
        failUnlessEqual('    Row = 110', lines[1])
        failUnlessEqual('        Col = 40', lines[2])
        failUnlessEqual('            Win[1] = 40', lines[3])
        failUnlessEqual('            Win[2] = 40', lines[4])
        failUnlessEqual('        Win[3] = 69', lines[5])
        failUnlessEqual('    Win[4] = 110', lines[6])
        failUnlessEqual('    Win[5] = 110', lines[7])

        lines = res.adjusted.describe()
        failUnlessEqual('Col = 110', lines[0])
        failUnlessEqual('    Row = 110', lines[1])
        failUnlessEqual('        Col = 44', lines[2])
        failUnlessEqual('            Win[1] = 44', lines[3])
        failUnlessEqual('            Win[2] = 44', lines[4])
        failUnlessEqual('        Win[3] = 65', lines[5])
        failUnlessEqual('    Win[4] = 110', lines[6])
        failUnlessEqual('    Win[5] = 110', lines[7])

    @test(testID='layout-adjust-sanity')
    def adjust_layout_sanely(self):
        """Layout adjustment avoids invalid widths and unwarranted adjustments.

        :<py>:

            from vpe import windows

            res = Struct()
            vpe.commands.split()
            vpe.commands.split()
            vpe.commands.split(vertical=True)
            vpe.commands.resize(-10, vertical=True)
            vim.options.columns += 10
            vpe.commands.split()
            res.layout = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())
            res.layout2 = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())
            res.layout3 = windows.LayoutElement.create_from_vim_layout(
                vim.winlayout())

            dump(res)
        """
        res = self.run_self()
        res.layout.adjust_width(3)
        lines = res.layout.describe()
        failUnlessEqual('Col = 3', lines[0])
        failUnlessEqual('    Row = 3', lines[1])
        failUnlessEqual('        Col = 1', lines[2])
        failUnlessEqual('            Win[1] = 1', lines[3])
        failUnlessEqual('            Win[2] = 1', lines[4])
        failUnlessEqual('        Win[3] = 1', lines[5])
        failUnlessEqual('    Win[4] = 3', lines[6])
        failUnlessEqual('    Win[5] = 3', lines[7])

        res.layout2.adjust_width(4)
        lines = res.layout2.describe()
        failUnlessEqual('Col = 4', lines[0])
        failUnlessEqual('    Row = 4', lines[1])
        failUnlessEqual('        Col = 1', lines[2])
        failUnlessEqual('            Win[1] = 1', lines[3])
        failUnlessEqual('            Win[2] = 1', lines[4])
        failUnlessEqual('        Win[3] = 2', lines[5])
        failUnlessEqual('    Win[4] = 4', lines[6])
        failUnlessEqual('    Win[5] = 4', lines[7])

        res.layout2.adjust_width(8)
        lines = res.layout2.describe()
        failUnlessEqual('Col = 8', lines[0])
        failUnlessEqual('    Row = 8', lines[1])
        failUnlessEqual('        Col = 3', lines[2])
        failUnlessEqual('            Win[1] = 3', lines[3])
        failUnlessEqual('            Win[2] = 3', lines[4])
        failUnlessEqual('        Win[3] = 4', lines[5])
        failUnlessEqual('    Win[4] = 8', lines[6])
        failUnlessEqual('    Win[5] = 8', lines[7])

        res.layout2[0].adjust_width(8)
        lines = res.layout2.describe()
        failUnlessEqual('Col = 8', lines[0])
        failUnlessEqual('    Row = 8', lines[1])
        failUnlessEqual('        Col = 3', lines[2])
        failUnlessEqual('            Win[1] = 3', lines[3])
        failUnlessEqual('            Win[2] = 3', lines[4])
        failUnlessEqual('        Win[3] = 4', lines[5])
        failUnlessEqual('    Win[4] = 8', lines[6])
        failUnlessEqual('    Win[5] = 8', lines[7])
