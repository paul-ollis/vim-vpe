"""Special handling of buffers."""
# pylint: disable=deprecated-method

from functools import partial

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support
import vim_if
from support import fix_path

import vpe

_run_after = ['test_vim.py']


class BuffersList(support.Base):
    """VPE support for the buffers list.

    The buffers list is actually more like a dictionary, keyed by integers,
    starting from 1. The use of :vim:`bwipeout` will leave gaps in the sequence
    of buffer numbers.
    """
    vim_buffers: vpe.wrappers.Buffers

    def suiteSetUp(self):
        """called to set up the suite."""
        super().suiteSetUp()
        self.vim_buffers = self.eval('vim.buffers')

    @test(testID='vim-buffers')
    def vim_buffers_list(self):
        """The buffers list object.

        :<py>:

            res = Struct()
            buffers = _vim.buffers
            res.init_len = len(buffers)
            bufadd('two')
            bufadd('three')
            res.len_three = len(buffers)

            vpe.commands.bwipeout('two')
            res.len_two = len(buffers)

            zap_bufs()
            res.len_one = len(buffers)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.init_len)
        failUnlessEqual(3, res.len_three)
        failUnlessEqual(2, res.len_two)
        failUnlessEqual(1, res.len_one)


class Buffers(support.Base):
    """VPE support for standard buffers.

    VPE provides the `Buffer` class that wraps a :vim:`python-buffer`. The
    Buffer may be used in the same manner as :vim:`python-buffer`, but has some
    enhancements.
    """
    buffer: vpe.wrappers.Buffer

    def suiteSetUp(self):
        """called to set up the suite."""
        super().suiteSetUp()
        self.buffer = self.eval('vim.current.buffer')

    @test(testID='buf-ro-attrs')
    def read_only_attrs(self):
        """Certain Buffer attributes are read-only."""
        buffer = self.buffer
        attrErrorCheck = partial(failUnlessRaises, AttributeError)
        attrErrorCheck(setattr, buffer, 'vars', buffer.vars)
        attrErrorCheck(setattr, buffer, 'options', buffer.options)
        attrErrorCheck(setattr, buffer, 'valid', buffer.valid)
        attrErrorCheck(setattr, buffer, 'number', buffer.number)

    @test(testID='buf-vars-attr')
    def buffer_vars_as_attributes(self):
        """Buffer.vars provides attribute style access.

        This is in addition to dictionary style access, making for more
        naturalistic code.

        :<py>:

            res = Struct()
            buffer = vim.current.buffer
            res.tick_one = buffer.vars.changedtick
            buffer.append('Another line')
            res.tick_two = buffer.vars.changedtick

            buffer.vars.new_var = 1234
            res.value = _vim.bindeval('b:new_var')

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.tick_two - res.tick_one)
        failUnlessEqual(1234, res.value)

    @test(testID='buf-options-attr')
    def buffer_options_as_attributes(self):
        """Buffer.options provides attribute style access.

        This is in addition to dictionary style access, making for more
        naturalistic code.

        :<py>:

            res = Struct()
            buffer = vim.current.buffer
            res.glob_ai = vim.options.autoindent
            buffer.options.autoindent = not vim.options.autoindent
            res.buf_ai = buffer.options.autoindent
            res.glob_ai_two = vim.options.autoindent

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(not res.glob_ai, res.buf_ai)
        failUnlessEqual(res.glob_ai, res.glob_ai_two)

    @test(testID='buf-name-change')
    def buffer_name_can_change(self):
        """Buffer.name can be modified.

        :<py>:

            res = Struct()
            buffer = vim.current.buffer
            res.orig_name = _vim.current.buffer.name
            buffer.name = '/tmp/monty'
            res.new_name = _vim.current.buffer.name

            dump(res)
        """
        res = self.run_self()
        failIfEqual(not res.orig_name, res.new_name)
        failUnlessEqual('/tmp/monty', fix_path(res.new_name))

    @test(testID='buf-valid-flag')
    def buffer_valid_flag(self):
        """Buffer.valid attribute is set to False when a buffer is wiped.

        :<py>:

            res = Struct()
            bufadd('/tmp/one')
            for b in vim.buffers:
                if b.name == '/tmp/one':
                    break
            res.orig_valid = b.valid
            vpe.commands.bwipeout(b.number)
            res.new_valid = b.valid

            dump(res)
        """
        res = self.run_self()
        failUnless(res.orig_valid)
        failIf(res.new_valid)

    @test(testID='buf-empty')
    def empty_buffer_has_one_line(self):
        """An empty buffer actually contains a single empty line.

        :<py>:

            res = Struct()
            buf = vim.current.buffer
            _buf = _vim.current.buffer
            _buf[:] = None
            res.len_buf = len(buf)
            res.line1 = buf[0]
            buf.append('Line 2')
            res.new_len_buf = len(buf)
            res.line2 = buf[-1]
            res.vim_new_len_buf = len(_buf)
            res.vim_line2 = _buf[-1]

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.len_buf)
        failUnlessEqual('', res.line1)
        failUnlessEqual(2, res.new_len_buf)
        failUnlessEqual(2, res.vim_new_len_buf)
        failUnlessEqual('Line 2', res.line2)
        failUnlessEqual('Line 2', res.vim_line2)

    @test(testID='buf-nr-insert')
    def insert_line_using_nr(self):
        """The *nr* argument can be used to insert a line.

        Note that, the vpe.Buffer allows nr to be used as a keyword argument.

        :<py>:

            res = Struct()
            buf = vim.current.buffer
            _buf = _vim.current.buffer
            _buf[:] = ['Line 1', 'Line 3']
            buf.append('Line 2', 1)
            buf.append('Line x', nr=0)
            res.lines = buf[:]

            dump(res)
        """
        res = self.run_self()
        lines = res.lines
        failUnlessEqual('Line x', lines[0])
        failUnlessEqual('Line 1', lines[1])
        failUnlessEqual('Line 2', lines[2])
        failUnlessEqual('Line 3', lines[3])

    @test(testID='buf-append-list')
    def append_list(self):
        """A list of lines can be appended.

        :<py>:

            res = Struct()
            buf = vim.current.buffer
            _buf = _vim.current.buffer
            buf[:] = []
            buf.append(['Line 1', 'Line 2'])
            buf.append(['Line 3', 'Line 4'])
            res.lines = buf[:]

            dump(res)
        """
        res = self.run_self()
        lines = res.lines
        failUnlessEqual('Line 1', lines[1])
        failUnlessEqual('Line 2', lines[2])
        failUnlessEqual('Line 3', lines[3])
        failUnlessEqual('Line 4', lines[4])

    @test(testID='buf-nr_insert_list')
    def insert_list_using_nr(self):
        """The *nr* argument can be used to insert a list of lines.

        :<py>:

            res = Struct()
            buf = vim.current.buffer
            _buf = _vim.current.buffer
            buf[:] = ['Line 1', 'Line 4']
            buf.append(['Line 2', 'Line 3'], nr=1)
            res.lines = buf[:]

            dump(res)
        """
        res = self.run_self()
        lines = res.lines
        failUnlessEqual('Line 1', lines[0])
        failUnlessEqual('Line 2', lines[1])
        failUnlessEqual('Line 3', lines[2])
        failUnlessEqual('Line 4', lines[3])

    @test(testID='buf-slice')
    def slicing(self):
        """Various slices work correctly.

        :<py>:

            res = Struct()
            buf = vim.current.buffer
            _buf = _vim.current.buffer
            _buf[:] = None

            res.empty_all = buf[:]
            buf[:] = ['Line 1', 'Line 4']
            res.one_four = buf[:]
            buf[1:1] = ['Line 2', 'Line 3']
            res.two_three = buf[1:3]
            buf.append('Line 5')
            del buf[1:4]
            res.one_five = buf[:]
            buf[:] = None
            res.empty_again = buf[:]

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual([''], res.empty_all)
        failUnlessEqual(['Line 1', 'Line 4'], res.one_four)
        failUnlessEqual(['Line 2', 'Line 3'], res.two_three)
        failUnlessEqual(['Line 1', 'Line 5'], res.one_five)
        failUnlessEqual([''], res.empty_again)

    @test(testID='buffer-marks')
    def buffer_marks(self):
        """The mark methods returns a mark's (row, col) tuple.

        :<py>:

            res = Struct()
            buf = vim.current.buffer

            buf[:] = [f'Line {i + 1}' for i in range(5)]
            win = _vim.current.window
            win.cursor = 2, 3
            _vim.command('normal ma')
            win.cursor = 4, 5
            res.mark = buf.mark('a')

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual((2, 3), res.mark)

    @test(testID='buf-list-context')
    def list_context(self):
        """The list context provides clean, efficient buffer modification.

        :<py>:

            res = Struct()
            buf = vim.current.buffer
            _buf = _vim.current.buffer

            # Just setting the contents.
            with buf.list() as b:
                b[:] = ['1', '2']
            res.one_two = buf[:]

            # Modifying the contents.
            with buf.list() as b:
                b.append('3')
            res.one_to_three = buf[:]

            # # Modifying the contents, even when buffer is not modifiable.
            _buf.options['modifiable'] = False
            try:
                try:
                    buf[:] = ['1', '2']
                except vim.error:
                    pass
                except:
                    pass
                res.still_one_to_three = buf[:]
                with buf.list() as b:
                    b.append('4')
                res.one_to_four = buf[:]
            finally:
                _buf.options['modifiable'] = True

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['1', '2'], res.one_two)
        failUnlessEqual(['1', '2', '3'], res.one_to_three)
        failUnlessEqual(['1', '2', '3'], res.still_one_to_three)
        failUnlessEqual(['1', '2', '3', '4'], res.one_to_four)

    @test(testID='temp-options-context')
    def temp_options_context(self):
        """The temp options context.

        The temp option values can be set using a context variables or by
        defining defaults.

        :<py>:

            res = Struct()
            buf = vim.current.buffer
            _buf = _vim.current.buffer

            res.orig_pi = _buf.options['preserveindent']
            with buf.temp_options() as opts:
                opts.preserveindent = not res.orig_pi
                res.temp_pi = _buf.options['preserveindent']
                res.temp_pi_lkup = opts['preserveindent']
                res.temp_pi_attr = opts.preserveindent
            res.restored_pi = _buf.options['preserveindent']

            with buf.temp_options(preserveindent=not res.orig_pi):
                res.temp_pi2 = _buf.options['preserveindent']
            res.restored_pi2 = _buf.options['preserveindent']

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(not res.orig_pi, res.temp_pi)
        failUnlessEqual(not res.orig_pi, res.temp_pi_lkup)
        failUnlessEqual(not res.orig_pi, res.temp_pi_attr)
        failUnlessEqual(res.orig_pi, res.restored_pi)
        failUnlessEqual(not res.orig_pi, res.temp_pi2)
        failUnlessEqual(res.orig_pi, res.restored_pi2)

    @test(testID='buf-range')
    def buffer_modified_using_range(self):
        """A buffer range allows access to the underlying buffer.

        Note that the range method's start and end are inclusive values.

        :<py>:

            res = Struct()
            buf = vim.current.buffer
            buf[:] = [str(n) for n in range(1, 10)]

            res.two_to_five = buf.range(2, 5)[:]
            rng = buf.range(2, 6)
            rng[0] = '22'
            rng[-1] = '66'
            rng[1:3] = ['a', 'b']
            res.mod_buf = buf[:]

            del buf.range(2, 5)[1:3]
            res.mod_buf2 = buf[:]

            rng = buf.range(2, 5)
            rng.append(['3', '4'], nr=1)
            rng.append('99')
            res.mod_buf3 = buf[:]

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['2', '3', '4', '5'], res.two_to_five)
        failUnlessEqual(
            ['1', '22', 'a', 'b', '5', '66', '7', '8', '9'], res.mod_buf)
        failUnlessEqual(
            ['1', '22', '5', '66', '7', '8', '9'], res.mod_buf2)
        failUnlessEqual(
            ['1', '22', '3', '4', '5', '66', '7', '99', '8', '9'],
            res.mod_buf3)

    @test(testID='buf-store')
    def arbitrary_data_can_be_stored(self):
        """There is an arbitrary data store for each buffer.

        The store is an aobject that allows arbitrary attribute assignment.
        Undefined attributes are ``None``.

        :<py>:

            res = Struct()
            buf_a = vim.current.buffer
            buf_b = get_alt_buffer()

            a = buf_a.store('test')
            b = buf_b.store('test')

            a.x = 3
            a.y = 'hello'
            b.x = a.x + 4

            res.a = vim.buffers[buf_a.number].store('test')
            res.b = vim.buffers[buf_b.number].store('test')
            res.none = b.monty

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(3, res.a.x)
        failUnlessEqual(7, res.b.x)
        failUnlessEqual('hello', res.a.y)
        failUnless(res.none is None)

    @test(testID='buf-type')
    def type_property(self):
        """The type property is a single word description.

        :<py>:

            res = Struct()
            res.normal_type = vim.current.buffer.type

            vpe.commands.enew()
            buf = vim.current.buffer
            buf.options.buftype = 'nofile'
            res.nofile_type = buf.type
            vpe.commands.bdelete('.')

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('normal', res.normal_type)
        failUnlessEqual('nofile', res.nofile_type)

    @test(testID='buf-location')
    def location_property(self):
        """The location property is the file's directory.

        If the buffer has no file then it is an empty string.

        :<py>:

            res = Struct()
            vpe.commands.edit('/tmp/nodir/nofile.txt')
            res.location = vim.current.buffer.location

            buf = vim.current.buffer
            buf.options.buftype = 'nofile'
            res.empty = buf.location
            vpe.commands.bdelete('.')

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('/tmp/nodir', fix_path(res.location))
        failUnlessEqual('', res.empty)

    @test(testID='buf-long-name')
    def long_display_name_property(self):
        """The long_display_name property depends on the buffer's type.

        :<py>:

            res = Struct()
            vpe.commands.cbuffer()
            vim.setqflist([], 'a', {'title': 'Test title'})
            vpe.commands.copen()
            res.qf = vim.current.buffer.long_display_name

            vpe.commands.edit('/tmp/nodir/nofile.txt')
            res.full_path = vim.current.buffer.long_display_name
            vpe.commands.bdelete('.')

            vpe.commands.enew()
            res.empty = vim.current.buffer.long_display_name
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('[quickfix]: Test title', res.qf)
        failUnlessEqual('/tmp/nodir/nofile.txt', fix_path(res.full_path))
        failUnlessEqual('[No name]', res.empty)

    @test(testID='buf-short-name')
    def short_display_name_property(self):
        """The short_display_name property depends on the buffer's type.

        :<py>:

            res = Struct()
            if vim.vvars.version >= 801:
                vpe.commands.terminal('echo')
                res.terminal = vim.current.buffer.short_display_name
                vpe.commands.bdelete('.')

            vpe.commands.edit('/tmp/nodir/nofile.txt')
            res.stem = vim.current.buffer.short_display_name
            vpe.commands.bdelete('.')

            vpe.commands.enew()
            res.empty = vim.current.buffer.short_display_name
            dump(res)
        """
        res = self.run_self()
        if vim_if.VimSession.get_version() >= [8, 1]:
            failUnlessEqual('[terminal]', res.terminal)
        failUnlessEqual('nofile.txt', res.stem)
        failUnlessEqual('[No name]', res.empty)

    @test(testID='buf-short_desc')
    def short_description_property(self):
        """The short_description property depends on the buffer's type.

        :<py>:

            res = Struct()
            vpe.commands.cbuffer()
            vim.setqflist([], 'a', {'title': 'Test title'})
            vpe.commands.copen()
            res.qf = vim.current.buffer.short_description

            vpe.commands.edit('/tmp/nodir/nofile.txt')
            res.location = vim.current.buffer.short_description
            vpe.commands.bdelete('.')

            if vim.vvars.version >= 801:
                vpe.commands.terminal('echo 9')
                res.terminal = vim.current.buffer.short_description
            vpe.commands.bdelete('.')
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('Test title', res.qf)
        failUnlessEqual('/tmp/nodir', fix_path(res.location))
        if vim_if.VimSession.get_version() >= [8, 1]:
            failUnlessEqual('!echo 9', res.terminal)

    @test(testID='buf-goto-same-window')
    def goto_same_window(self):
        """The goto_active_window method prefers the current window.

        Otherwise is uses the lowest numbered matching window.
        :<py>:

            res = Struct()
            res.r = []
            vpe.commands.tabonly()
            vpe.commands.wincmd('o')

            vpe.commands.wincmd('s')
            w1 = vim.current.window
            b1 = vim.current.buffer
            vpe.commands.wincmd('w', a=2)
            w2 = vim.current.window

            vpe.commands.wincmd('s')
            vpe.commands.wincmd('w', a=3)
            vpe.commands.enew()
            b2 = vim.current.buffer

            vpe.commands.wincmd('w', a=1)
            res.r.append(b1.goto_active_window())
            res.same_win = vim.current.window.number

            vpe.commands.wincmd('w', a=2)
            res.r.append(b1.goto_active_window())
            res.same_win2 = vim.current.window.number

            vpe.commands.wincmd('w', a=3)
            res.r.append(b1.goto_active_window())
            res.same_win3 = vim.current.window.number

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.same_win)
        failUnlessEqual(2, res.same_win2)
        failUnlessEqual(1, res.same_win3)
        failUnlessEqual([True, True, True], res.r)

    @test(testID='buf-goto-search-tabs')
    def goto_same_search_tabs(self):
        """The goto_active_window will use a different tab.

        The lowest numbered tab is preferred. If no window is found then
        nothing changes and False is returned.
        :<py>:

            res = Struct()
            res.r = []
            vpe.commands.tabonly()
            vpe.commands.wincmd('o')
            t1 = vim.current.tabpage
            hidden_buf = vim.current.buffer
            vpe.commands.tabnew()
            t2 = vim.current.tabpage
            vpe.commands.tabnew()
            t3 = vim.current.tabpage
            vpe.commands.tabnew()
            t4 = vim.current.tabpage

            vpe.commands.tabnext(a=2)
            vpe.commands.enew()
            target = vim.current.buffer

            vpe.commands.tabnext(a=4)
            vpe.commands.buffer(target.number)

            vpe.commands.tabnext(a=3)
            res.start_tab = vim.current.tabpage.number
            res.r.append(target.goto_active_window())
            res.tab_found = vim.current.tabpage.number

            vpe.commands.tabnext(a=1)
            vpe.commands.tabclose()
            vpe.commands.tabnext(a=2)
            res.start_tab2 = vim.current.tabpage.number
            res.r.append(hidden_buf.goto_active_window())
            res.end_tab = vim.current.tabpage.number

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(3, res.start_tab)
        failUnlessEqual(2, res.tab_found)
        failUnlessEqual(2, res.start_tab2)
        failUnlessEqual(2, res.end_tab)
        failUnlessEqual([True, False], res.r)

    def setup_tabs_and_windows(self):
        """Set up a well defined pattern of windows and tab pages.

        :<py>:
            vpe.commands.tabonly()
            vpe.commands.wincmd('o')
            t1 = vim.current.tabpage
            hidden_buf = vim.current.buffer
            vpe.commands.tabnew()
            t2 = vim.current.tabpage
            vpe.commands.tabnew()
            t3 = vim.current.tabpage
            vpe.commands.tabnew()
            t4 = vim.current.tabpage

            vpe.commands.tabnext(a=2)
            vpe.commands.enew()
            vpe.commands.wincmd('s')
            target = vim.current.buffer

            vpe.commands.tabnext(a=4)
            vpe.commands.buffer(target.number)
        """
        self.run_self()

    @test(testID='buf-find-active-any')
    def find_active_any_tab(self):
        """The find_active_windows method will search all tabs.

        The order of windows returned is well defined.

        :<py>:

            res = Struct()
            res.find_all_cur_first = [
                (w.tabpage.number, w.number)
                for w in target.find_active_windows()]

            vpe.commands.tabnext(a=3)
            res.find_all = [
                (w.tabpage.number, w.number)
                for w in target.find_active_windows()]

            vpe.commands.tabnext(a=2)
            vpe.commands.wincmd('j', a=2)
            res.find_all_cur_tab_second = [
                (w.tabpage.number, w.number)
                for w in target.find_active_windows()]
            dump(res)
        """
        self.setup_tabs_and_windows()
        res = self.run_self()
        failUnlessEqual([(4, 1), (2, 1), (2, 2)], res.find_all_cur_first)
        failUnlessEqual([(2, 1), (2, 2), (4, 1)], res.find_all)
        failUnlessEqual([(2, 2), (2, 1), (4, 1)], res.find_all_cur_tab_second)

    @test(testID='buf-find-cur-tab')
    def find_active_cur_tab(self):
        """The find_active_windows method can search just the current tab page.

        :<py>:

            res = Struct()
            vpe.commands.tabnext(a=3)
            res.find_zero = [
                (w.tabpage.number, w.number)
                for w in target.find_active_windows(all_tabpages=False)]

            vpe.commands.tabnext(a=2)
            res.find_two = [
                (w.tabpage.number, w.number)
                for w in target.find_active_windows(all_tabpages=False)]
            dump(res)
        """
        self.setup_tabs_and_windows()
        res = self.run_self()
        failUnlessEqual([], res.find_zero)
        failUnlessEqual([(2, 1), (2, 2)], res.find_two)

    @test(testID='buf-info')
    def getbufinfo_as_properties(self):
        """The getbufinfo() values appear as properties.

        There are a few exceptions. This test just checks a few values
        because all values use the same implementation code.
        :<py>:

            res = Struct()

            buf = vim.current.buffer
            buf[:] = ['1', '2']
            if vim.has('patch-8.2.0019'):
                res.nlines = buf.linecount
            res.loaded = buf.loaded
            res.lnum = buf.lnum
            try:
                res.nothing = buf.wibble
            except AttributeError:
                res.nothing = 'Nothing'
            dump(res)
        """
        res = self.run_self()
        if vim_if.VimSession.has_patch("patch-8.2.0019"):
            failUnlessEqual(2, res.nlines)
        failUnlessEqual(1, res.loaded)
        failUnlessEqual(1, res.lnum)
        failUnlessEqual('Nothing', res.nothing)


if __name__ == '__main__':
    runModule()
