"""The vpe.mapping module.

VPE supports creating key mappings that execute Python functions.

Mappings can be created for normal (nmap), visual (xmap), operator-pending
(omap) and insert (imap) modes. The other modes are not supported until
such time that practical use cases are identified.
"""
# pylint: disable=deprecated-method

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support
import vim_if

import vpe

_run_after = ['test_vim.py']


class Mapping(support.Base):
    """Base for mapping tests."""

    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            from vpe import commands

            commands.wincmd('o')
            commands.buffer('1')
        """
        super().suiteSetUp()
        self.run_self()

    def tearDown(self):
        r"""Clean up after each test.

        :<py>:

            # Ensure normal mode is restored.
            vpe.feedkeys(r'\<C-\>\<C-N>')
        """
        return self.run_self()

    def run_mapping(self):
        """Run the script for a mapping test.

        The execution of the Python code for a mapping test must be split up
        so that Vim gets a chance to process buffered keys.

        :<py>:

            res.lines = list(vim.current.buffer)
            dump(res)
        """
        code_text, _ = self.mycode(stack_level=2)
        self.vs.execute_python_code(code_text)
        return self.run_self()


class NormalMapping(Mapping):
    """Normal mode mappings."""

    def tearDown(self):
        r"""Clean up after each test.

        :<py>:

            # Ensure normal mode is restored.
            vpe.commands.nunmap('<buffer> f')
            vpe.commands.nunmap('f')
        """
        super().tearDown()
        self.run_self()

    @test(testID='simple-mapping')
    def simple_mapping(self):
        """A simple normal mode mapping of a standard key.

        :<py>:

            from vpe.mapping import nmap

            def handle(info):
                res.info = info
                res.info_str = str(info)

            res = Struct()
            nmap('f', handle)
            vpe.feedkeys(r'f', literal=True)
        """
        res = self.run_mapping()
        info = res.info
        failUnlessEqual('f', info.keys)
        failUnlessEqual('normal', info.mode)
        failUnless(info.vmode is None)
        failUnlessEqual((-1, -1), info.start_cursor)
        failUnlessEqual((-1, -1), info.end_cursor)
        failUnless(info.line_range is None)
        failUnlessEqual('MappingInfo(normal,f)', res.info_str)

    @test(testID='simple-mapping-to_str')
    def simple_mapping_str(self):
        """A mapping may simply map to a string.

        :<py>:

            from vpe.mapping import nmap

            res = Struct()
            res.value = 0
            vim.vars.vpe_test_var = 0
            nmap('f', ':py3 res.value = 1<CR>')
            vpe.feedkeys(r'f', literal=True)
        """
        res = self.run_mapping()
        failUnlessEqual(1, res.value)

    @test(testID='special-key-mapping')
    def special_key_mapping(self):
        r"""A normal mode mapping of a special key.

        :<py>:

            from vpe.mapping import nmap

            def handle(info):
                res.info = info

            res = Struct()
            nmap('<F4>', handle)
            vpe.feedkeys(r'\<F4>')
        """
        res = self.run_mapping()
        info = res.info
        failUnlessEqual('<F4>', info.keys)
        failUnlessEqual('normal', info.mode)
        failUnless(info.vmode is None)
        failUnlessEqual((-1, -1), info.start_cursor)
        failUnlessEqual((-1, -1), info.end_cursor)
        failUnless(info.line_range is None)

    @test(testID='non-info-mapping')
    def simple_non_info_mapping(self):
        """A simple normal mode mapping that does not pass info.

        :<py>:

            from vpe.mapping import nmap

            def handle():
                res.called = 1

            res = Struct()
            nmap('f', handle, pass_info=False)
            vpe.feedkeys(r'f', literal=True)
        """
        res = self.run_mapping()
        failUnlessEqual(1, res.called)

    @test(testID='non-buffer-mapping')
    def simple_non_buffer_mapping(self):
        """Mappings can be global, rather limited to the current buffer.

        :<py>:

            from vpe.mapping import nmap

            def handle(info):
                res.called = 1

            res = Struct()
            nmap('f', handle, buffer=False)
            vpe.feedkeys(r'f', literal=True)
        """
        res = self.run_mapping()
        failUnlessEqual(1, res.called)

    def del_handle(self):
        """Continue execution, saving the result structure.

        :<py>:
            del handle
            vpe.feedkeys(r'f', literal=True)
            dump(res)
        """
        return self.run_mapping()

    @test(testID='non-mapping-remove-for-dead-function')
    def mapping_is_removed_for_dead_function(self):
        """Mappings are removed if the mapped function disappears.

        :<py>:
            print("START")
            from vpe.mapping import nmap

            def handle(info):
                res.called += 1
                print("INV", res.called)

            res = Struct()
            res.called = 0
            nmap('f', handle)
            vpe.feedkeys(r'f', literal=True)
        """
        res = self.run_mapping()
        failUnlessEqual(1, res.called)
        res = self.del_handle()
        failUnlessEqual(1, res.called)

    @test(testID='non-mapping-remove-for-dead-function-non-buffer')
    def mapping_is_removed_for_dead_function_non_buffer(self):
        """Mappings are removed if the mapped function disappears.

        :<py>:
            print("START")
            from vpe.mapping import nmap

            def handle(info):
                res.called += 1
                print("INV", res.called)

            res = Struct()
            res.called = 0
            nmap('f', handle, buffer=False)
            vpe.feedkeys(r'f', literal=True)
        """
        res = self.run_mapping()
        failUnlessEqual(1, res.called)
        res = self.del_handle()
        failUnlessEqual(1, res.called)


class VisualMapping(Mapping):
    """Visual mode mappings."""
    @test(testID='line-range-mapping')
    def line_range_mapping(self):
        """A visual mode mapping with a lines selection.

        :<py>:

            from vpe.mapping import xmap

            def handle(info):
                res.info = info

            res = Struct()
            xmap('f', handle)

            buf = vim.current.buffer
            buf[:] = [
                'Unused',
                'Hello',
                'World',
                'Unused',
            ]
            vim.current.window.cursor = (2, 2)
            vpe.feedkeys(''.join(('V', 'j', 'f')), literal=True)
        """
        res = self.run_mapping()
        info = res.info
        failUnlessEqual('f', info.keys)
        failUnlessEqual('visual', info.mode)
        failUnlessEqual('line', info.vmode)
        failUnlessEqual((2, 1), info.start_cursor)
        failUnlessEqual((3, 0x7fffffff), info.end_cursor)
        failUnlessEqual((1, 3), info.line_range)

    @test(testID='char-range-mapping')
    def char_range_mapping(self):
        """A visual mode mapping with a character selection.

        :<py>:

            from vpe.mapping import xmap

            def handle(info):
                res.info = info

            res = Struct()
            xmap('f', handle)

            buf = vim.current.buffer
            buf[:] = [
                'Unused',
                'xxHello',
                'Worldxxx',
            ]
            vim.current.window.cursor = (2, 2)
            vpe.feedkeys(''.join(('v', 'j', 'll', 'f')), literal=True)
        """
        res = self.run_mapping()
        info = res.info
        failUnlessEqual('f', info.keys)
        failUnlessEqual('visual', info.mode)
        failUnlessEqual('character', info.vmode)
        failUnlessEqual((2, 3), info.start_cursor)
        if vim_if.VimSession.get_version() >= [8, 1]:
            # There seems to be a problem reliably feeding keys in 8.0.*.
            failUnlessEqual((3, 5), info.end_cursor)
        failUnlessEqual((1, 3), info.line_range)

    @test(testID='block-range-mapping')
    def block_range_mapping(self):
        r"""A visual mode mapping with a block selection.

        :<py>:

            from vpe.mapping import xmap

            def handle(info):
                res.info = info
                res.selction = vim.current

            res = Struct()
            xmap('f', handle)

            buf = vim.current.buffer
            buf[:] = [
                'Unused',
                'xxHelloxxx',
                'xxWorldxxx',
            ]
            vim.current.window.cursor = (2, 2)
            vpe.feedkeys(''.join((r'\<C-V>', 'j', 'llll', 'f')))
        """
        res = self.run_mapping()
        info = res.info
        failUnlessEqual('f', info.keys)
        failUnlessEqual('visual', info.mode)
        failUnlessEqual('block', info.vmode)
        failUnlessEqual((2, 3), info.start_cursor)
        failUnlessEqual((3, 7), info.end_cursor)
        failUnlessEqual((1, 3), info.line_range)


class InsertMapping(Mapping):
    """Insert mode mappings."""

    @test(testID='insert-mapping')
    def insert_mapping(self):
        """A simple insert mode mapping of a standard key.

        :<py>:

            from vpe.mapping import imap

            def handle(info):
                res.info = info
                return 'Hello'

            res = Struct()
            imap('f', handle)

            buf = vim.current.buffer
            buf[:] = []

            vpe.feedkeys(r'if', literal=True)
        """
        res = self.run_mapping()
        info = res.info
        failUnlessEqual('f', info.keys)
        failUnlessEqual('insert', info.mode)
        failUnless(info.vmode is None)
        failUnlessEqual((-1, -1), info.start_cursor)
        failUnlessEqual((-1, -1), info.end_cursor)
        failUnless(info.line_range is None)
        failUnlessEqual('Hello', res.lines[0])

    @test(testID='insert-cmd-mapping')
    def insert_cmd_mapping(self):
        """An insert mode mapping executed in command mode.

        In this case, insert mode has been left before the function is invoked.

        :<py>:

            from vpe.mapping import imap

            def handle(info):
                res.info = info
                return 'Hello'

            res = Struct()
            imap('f', handle, command=True)

            buf = vim.current.buffer
            buf[:] = []

            vpe.feedkeys(r'if', literal=True)
        """
        res = self.run_mapping()
        info = res.info
        failUnlessEqual('f', info.keys)
        failUnlessEqual('insert', info.mode)
        failUnless(info.vmode is None)
        failUnlessEqual((-1, -1), info.start_cursor)
        failUnlessEqual((-1, -1), info.end_cursor)
        failUnless(info.line_range is None)
        failUnlessEqual('', res.lines[0])


class OpPendingMapping(Mapping):
    """Operator pending mode mappings."""

    @test(testID='pending-mapping')
    def pending_mapping(self):
        """A simple operator pending mode mapping of a standard key.

        :<py>:

            from vpe.mapping import omap

            def handle(info):
                res.info = info

            res = Struct()
            omap('f', handle)
            vpe.feedkeys(r'yf', literal=True)
        """
        res = self.run_mapping()
        info = res.info
        failUnlessEqual('f', info.keys)
        failUnlessEqual('op-pending', info.mode)
        failUnless(info.vmode is None)
        failUnlessEqual((-1, -1), info.start_cursor)
        failUnlessEqual((-1, -1), info.end_cursor)
        failUnless(info.line_range is None)


class ErrorConditions(Mapping):
    """Handling of error conditions."""

    @test(testID='invalid-mode')
    def map_with_bad_mode(self):
        """Using map with an unsupported mode raise NotImplementedError.

        :<py>:

            from vpe.mapping import map

            def handle(info):
                res.info = info

            res = Struct()
            res.raised = None
            try:
                map('select', 'f', handle)
            except Exception as e:
                res.raised = e
        """
        res = self.run_mapping()
        failUnless(isinstance(res.raised, NotImplementedError))

    @test(testID='callback-exception')
    def callback_exception(self):
        """An exception in a callback is gracefully handled.

        :<py>:

            from vpe.mapping import nmap

            def handle(info):
                res.info = info
                assert False

            res = Struct()
            res.raised = None
            nmap('f', handle)
            vpe.feedkeys('f', literal=True)

        """
        # TODO: Need a machanism to verify the error was handled.
        #       Currently this is just doing noddy code coverage.
        res = self.run_mapping()

    @test(testID='dead-callback')
    def dead_callback(self):
        """An dead callback is gracefully handled.

        :<py>:

            from vpe.mapping import nmap

            def handle(info):
                res.info = info

            res = Struct()
            res.raised = None
            nmap('f', handle)
            del handle
            vpe.feedkeys('f', literal=True)
        """
        # TODO: Need a machanism to verify the error was handled.
        #       Currently this is just doing noddy code coverage.
        res = self.run_mapping()


if __name__ == '__main__':
    runModule()
