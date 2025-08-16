"""Function style execution of vim commands."""
# pylint: disable=deprecated-method

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.DataMaker import literalText2Text
from cleversheep3.Test.Tester import *

import support

_run_after = ['test_vim.py']


class Commands(support.Base):
    """VPE support for exeuting commands using functions calls.

    The vpe.commands module provide function equivalents for most Ex commands.
    """
    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            from vpe import commands

            commands.enew()
        """
        super().suiteSetUp()
        self.run_self()

    @test(testID='command-a')
    def run_command_on_single_line(self):
        """A command can be run on a single line.

        :<py>:

            from vpe import commands

            res = Struct()

            buf = vim.current.buffer
            buf[:] = [str(i) for i in range(1, 11)]
            commands.delete(a=9)
            res.a = list(buf[7:])

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['8', '10'], res.a)

    @test(testID='command-b')
    def run_command_from_dot_to_b(self):
        """Just the end line can be specified; the start is the current line.

        :<py>:

            from vpe import commands

            res = Struct()

            buf = vim.current.buffer
            buf[:] = [str(i) for i in range(1, 11)]
            vim.current.window.cursor = 2, 0
            commands.delete(b=3)
            res.b = list(buf[0:2])

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['1', '4'], res.b)

    @test(testID='command-a-b')
    def run_command_from_a_to_b(self):
        """Args a and b can specify the range; lrange is ignored.

        :<py>:

            from vpe import commands

            res = Struct()

            buf = vim.current.buffer
            buf[:] = [str(i) for i in range(1, 11)]
            commands.delete(a=2, b=3, lrange=(1,5))
            res.b = list(buf[0:2])

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['1', '4'], res.b)

    @test(testID='command-tuple')
    def run_command_with_tuple_range(self):
        """The lrange arg can be a tuple.

        :<py>:

            from vpe import commands

            res = Struct()

            buf = vim.current.buffer
            buf[:] = [str(i) for i in range(1, 11)]
            commands.delete(lrange=(2, 3))
            res.b = list(buf[0:2])

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['1', '4'], res.b)

    @test(testID='command-range')
    def run_command_with_python_range(self):
        """The lrange arg can be a Python range.

        :<py>:

            from vpe import commands

            res = Struct()

            buf = vim.current.buffer
            buf[:] = [str(i) for i in range(1, 11)]
            commands.delete(lrange=range(1, 3))
            res.b = list(buf[0:2])

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['1', '4'], res.b)

    @test(testID='command-string')
    def run_command_with_string_range(self):
        """The lrange arg can be a simple string.

        :<py>:

            from vpe import commands

            res = Struct()

            buf = vim.current.buffer
            buf[:] = [str(i) for i in range(1, 11)]
            commands.delete(lrange='2,3')
            res.b = list(buf[0:2])

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['1', '4'], res.b)

    @test(testID='command-args')
    def run_command_with_reg_arg(self):
        """Command arguments can be used.

        :<py>:

            from vpe import commands

            res = Struct()

            buf = vim.current.buffer
            buf[:] = [str(i) for i in range(1, 11)]
            commands.delete('r', lrange=range(1, 3))
            res.r = vim.registers['r']

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('2\n3\n', res.r)

    @test(testID='command-mods')
    def run_command_with_modifiers(self):
        """Command modifiers are suported.

        The modifiers are vertical, aboveleft, belowright, topleft, botright
        and keepalt.

        :<py>:

            from vpe import commands

            res = Struct()

            commands.wincmd('o')
            commands.wincmd('s', botright=True)
            res.win_num = vim.current.window.number

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(2, res.win_num)

    @test(testID='command-mods-2')
    def run_command_with_baked_modifiers(self):
        """Command modifiers can be 'baked in' using ``with_modifiers``.

        :<py>:

            from vpe import commands

            res = Struct()

            commands.wincmd('o')
            botright = commands.with_modifiers(botright=True)
            botright.wincmd('s')
            res.win_num = vim.current.window.number

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(2, res.win_num)

    @test(testID='command-keepalt')
    def run_command_keepalt(self):
        """The keepalt modifier is true by default.

        :<py>:

            from vpe import commands

            res = Struct()

            commands.wincmd('o')
            res.orig_alt = vim.registers['#']
            commands.edit('/tmp/vpe-wiley.txt')
            res.new_alt = vim.registers['#']
            res.new_buf = vim.current.buffer.name

            commands.edit('/tmp/vpe-wilier.txt', keepalt=False)
            res.newer_alt = vim.registers['#']

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.orig_alt, res.new_alt)
        failUnlessEqual(res.orig_alt, res.new_alt)
        failIfEqual(res.orig_alt, res.newer_alt)
        expected = res.new_buf[2:] if res.new_buf[1] == ':' else res.new_buf
        failUnlessEqual(expected, res.newer_alt)

    @test(testID='command-unknown')
    def unknown_comand_is_attributue_error(self):
        """An unknown command is raises an AttributeError.

        :<py>:

            from vpe import commands

            res = Struct()
            try:
                func = commands.no_such_command
                res.v = func
            except AttributeError as e:
                res.v = e
            try:
                func = commands.__iter__
                res.v2 = func
            except AttributeError as e:
                res.v2 = e

            dump(res)
        """
        res = self.run_self()
        failUnless(isinstance(res.v, AttributeError))
        failUnless(isinstance(res.v2, AttributeError))


class VpeCommands(support.Base):
    """VPE provides a ``Vpe``, which is composed of a number of subcommands."""

    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            import vpe
            from vpe import vpe_commands

            vpe_commands.init()
            vpe.log.clear()
        """
        super().suiteSetUp()
        self.run_self()

    def setUp(self):
        """Called to prepare for a test.

        :<py>:

            import vpe
            vim.options.cmdheight = 10
        """
        super().setUp()
        self.run_self()

    def tearDown(self):
        """Called to clean up after a test.

        :<py>:

            import vpe

            vpe.log.redirect()
            vpe.log.set_maxlen(500)
            vpe.commands.redir('END')
            vim.options.cmdheight = 2
        """
        super().tearDown()
        self.run_self()

    def cleanup_screen(self):
        """Contine executions to allow things to flush.

        :<py>:

            vpe.commands.redraw()
        """
        return self.run_continue()

    @test(testID='vpe-commands-insert_config')
    def vpe_insert_config(self):
        """Command ``Vpe insert_config`` inserts a basic configuration.

        The configuration is inserted into the current buffer.

        :<py>:

            res = Struct()
            vim.current.buffer[:] = []
            vpe.vim.command('Vpe insert_config')
            res.lines = list(vim.current.buffer)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqualStrings(
            literalText2Text('''
                | " The VPE configuration structure.
                | let g:vpe_config = {}
                | let g:vpe_config.import = {}
                |
                | " Import `vpe` imported into Vim's python namespace.
                | let g:vpe_config.import.vpe = 1
                |
                | " Import `vim` (the `Vim` singleton) into Vim's python
                | " namespace.
                | let g:vpe_config.import.vim = 1
                |
                | " Import `vpe` into Pythons's builtins namespace.
                | let g:vpe_config.import.vpe_into_builtins = 1
                |
                | " Import `vim` (the `Vim` singleton) into Python's builtins
                | " namespace.
                | let g:vpe_config.import.vim_into_builtins = 1
            '''),
            '\n'.join(res.lines)
        )

    @test(testID='vpe-commands-insert_config-vim9')
    def vpe_insert_config_vim9(self):
        """Command ``Vpe insert_config`` adjusts for an obvious vim9 script.

        :<py>:

            res = Struct()
            vim.current.buffer[:] = ['vim9script', '']
            vpe.commands.normal('G')
            vpe.vim.command('Vpe insert_config')
            res.lines = list(vim.current.buffer)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqualStrings(
            literalText2Text('''
                | vim9script
                | # The VPE configuration structure.
                | var g:vpe_config = {}
                | g:vpe_config.import = {}
                |
                | # Import `vpe` imported into Vim's python namespace.
                | g:vpe_config.import.vpe = 1
                |
                | # Import `vim` (the `Vim` singleton) into Vim's python
                | # namespace.
                | g:vpe_config.import.vim = 1
                |
                | # Import `vpe` into Pythons's builtins namespace.
                | g:vpe_config.import.vpe_into_builtins = 1
                |
                | # Import `vim` (the `Vim` singleton) into Python's builtins
                | # namespace.
                | g:vpe_config.import.vim_into_builtins = 1
            '''),
            '\n'.join(res.lines)
        )

    @test(testID='vpe-commands-log-show-hide')
    def vpe_log_show_hide(self):
        r"""Command ``Vpe log show/hide`` shows or hides the log buffer.

        The log is shown in a split window.

        :<py>:

            res = Struct()
            vpe.commands.wincmd('o')
            res.init_win_count = len(vim.windows)

            vpe.vim.command('Vpe log show')
            res.log_win_count_a = len(vim.windows)
            vpe.log.clear()
            vpe.log.write('Hello\n')
            vpe.commands.wincmd('w')
            res.lines = list(vim.current.buffer)

            vpe.commands.wincmd('w')
            vpe.vim.command('Vpe log hide')
            res.log_win_count_b = len(vim.windows)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.init_win_count)
        failUnlessEqual(2, res.log_win_count_a)
        failUnlessEqual(1, res.log_win_count_b)
        failUnless(res.lines[1].endswith(': Hello'))

    @test(testID='vpe-commands-redirect-on-off')
    def vpe_log_redirect_off_on(self):
        r"""Command ``Vpe log redirect on/off`` controls stdout redirection.

        And also stderr redirection. The current redirection state is queried
        using ``Vpe log redirect``.

        :<py>:

            import sys

            res = Struct()

            # vpe.commands.command('redir @a>')
            # vpe.vim.command('silent! Vpe log redirect')

            vpe.log.clear()
            vpe.vim.command('silent! Vpe log redirect off')
            # vpe.vim.command('silent! Vpe log redirect')
            print('Hello')
            print('Hello friend!', file=sys.stderr)
            vpe.vim.command('silent! Vpe log redirect on')
            print('Goodbye')
            print('Goodbye friend!', file=sys.stderr)

            #vpe.commands.command('redir END')
            res.lines = vpe.log.lines
            #res.register_a = vim.registers['a']
            dump(res)
            vpe.commands.redraw()
        """
        # TODO: I am not getting as much captured message output as expected.
        #       I think the solution is for the Vpe command to take account of
        #       the silent modifier and apply it to echo_msg, but that is
        #       tedious so perhaps some sort of 'silent tracking' is in order,
        #       which affects the behaviour of echo_msg.
        #
        #       Currently it seems that trying to capture to a register is
        #       fragile. Some a number of tests here are crippled.
        #
        res = self.run_self()
        self.cleanup_screen()
        print(res.lines)
        failUnlessEqual(2, len(res.lines))
        failIf(res.lines[0].endswith(': Hello'))
        failUnless(res.lines[0].endswith(': Goodbye'))
        failUnless(res.lines[1].endswith(': Goodbye friend!'))
        # failUnlessEqualStrings(
        #    literalText2Text('''
        #    |
        #    | Stdout/stderr being redirected to the log
        #    | Stdout/stderr not being redirected to the log
        #    '''),
        #    res.register_a
        #)

    @test(testID='vpe-commands-log-length')
    def vpe_log_length(self):
        r"""Command ``Vpe log length ...`` controls the log length.

        The current log maximum length is queried by ``Vpe log length``.

        :<py>:

            import sys

            res = Struct()

            vpe.log.clear()
            vpe.vim.command('Vpe log length 3')
            for n in range(4):
                print(f'Hello {n}')

            vpe.vim.command('Vpe log length')
            res.lines = vpe.log.lines
            dump(res)
        """
        # TODO: See vpe_log_redirect_off_on for how to capture echo_msg output
        #       correctly. This test has some simplistic coverage without
        #       checking!
        res = self.run_self()
        print(res.lines)
        failUnlessEqual(3, len(res.lines))
        failUnless(res.lines[0].endswith(': Hello 1'))
        failUnless(res.lines[1].endswith(': Hello 2'))
        failUnless(res.lines[2].endswith(': Hello 3'))

    @test(testID='vpe-commands-log-length')
    def vpe_version(self):
        r"""Command ``Vpe version`` simply shows the version.

        The current log maximum length is queried by ``Vpe log length``.

        :<py>:

            res = Struct()
            vpe.vim.command('Vpe version')
            dump(res)
        """
        # TODO: See vpe_log_redirect_off_on for how to capture echo_msg output
        #       correctly. This test is simplistic coverage without checking!
        _res = self.run_self()
