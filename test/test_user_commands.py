"""Tests for the VPE user_commands based user command support."""

# pylint: disable=unused-wildcard-import,wildcard-import
# pylint: disable=deprecated-method
# pylint: disable=wrong-import-order

import re

from cleversheep3.Test.DataMaker import literalText2Text
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester.PollTester import *

import vpe
from vpe import user_commands, common
from vpe.user_commands import (
    CommandHandler, SimpleCommandHandler, SubcommandHandlerBase,
    TopLevelSubcommandHandler, VimCommandHandler)

_run_after = ['test_vim.py']


class Struct:
    """A basic data storage structure."""


class CommandBase(PollSuite):
    """Base for user_commands module tests."""
    # pylint: disable=missing-class-docstring,missing-function-docstring
    # pylint: disable=attribute-defined-outside-init

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.help_dest=  []
        self.commands = []

    @property
    def help_str(self) -> str:
        return '\n'.join(self.help_dest)

    @property
    def error_message(self) -> str:
        """The first error message."""
        command = self.extract_command('^echohl ErrorMsg$')
        if command:
            command = self.extract_command('^echomsg ', after=command)
            if command:
                return command[9:-1]
        return ''

    def on_command(self, cmd: str):
        """Callback for when vim.command is invoked.

        :cmd: The command that was run.
        """
        self.commands.append(cmd)

    def extract_command(self, pattern: str, after: str = '') -> str:
        """Extract a command using a search pattern."""
        if after:
            for command in self.commands:
                if command == after:
                    break
            else:
                return ''

        for command in self.commands:
            if re.search(pattern, command):
                return command
        return ''

    def dump_commands(self) -> None:
        """Dump all commands to the log - only for test debugging."""
        for command in self.commands:
            print(f'Command: {command}')

    def suiteSetUp(self):
        """Suite init function."""
        super().suiteSetUp()
        vpe.vim.vim().register_command_callback(self.on_command)
        vpe.vim.vim().poll_man = self.pollMan

    def suiteTearDown(self):
        """Suite clean up function."""
        super().suiteTearDown()
        vpe.vim.vim().register_command_callback(None)
        #vpe.common.id_source = self.saved_id_source

    def setUp(self):
        """Per test init function."""
        self.help_dest[:] = []
        user_commands.help_dest = self.help_dest
        self.commands = []

        # TODO:
        #     This clean up after non-poll manager tests, which may leave an
        #     call_soon functions. I would prefe a cleaner way.
        common._scheduled_soon_calls[:] = []
        ##self.saved_id_source = vpe.common.id_source
        #vpe.common.id_source = itertools.count(100)

    def tearDown(self):
        """Per test clean up."""
        user_commands.help_dest = None
        #vpe.common.id_source = self.saved_id_source

    #@pollAware
    def assertNoErrorMessages(self) -> None:
        yield self.delay(0.0)
        if self.error_message:
            fail(f'Unexpected error: {self.error_message}')


class SubCommandFormation(CommandBase):
    """Formation and execution of commands with subcommands."""
    # pylint: disable=missing-class-docstring,missing-function-docstring
    # pylint: disable=attribute-defined-outside-init

    @test(testID='commands-simple')
    def simple_subcommand(self):
        """A simple subcommand can be created and executed.

        Subcommand names can be abbreviated.
        """

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (':simple', 'Say hello.'),
            }

            def handle_hello(self, args):
                res.args = args

        command = Command('Test')

        res = Struct()
        command.handle_main_command(None, 'hello')
        failIf(res.args is None)
        failUnlessEqual('hello', res.args.subcommand)

        res = Struct()
        command.handle_main_command(None, 'he')
        failIf(res.args is None)
        failUnlessEqual('hello', res.args.subcommand)

    @test(testID='commands-missing-subcommand')
    def simple_subcommand_help(self):
        """A simple subcommand has auto-generated help."""

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (':simple', 'Say hello.'),
            }

            def handle_hello(self, args):
                res.args = args

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None, '--help')
        yield self.delay(0.0)
        failUnlessEqualStrings(literalText2Text('''
          | Usage: Test [-h] subcommand
          |
          | Subcommands:
          |    hello - Say hello.
          | options:
          |   -h, --help  Show this help message.
        '''), self.help_str)

    @test(testID='commands-missing-subcommand-error')
    def missing_subcommand(self):
        """A missing subcommand produces an error message."""

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (':simple', 'Say hello.'),
            }

            def handle_hello(self, args):
                res.args = args

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None)
        yield self.delay(0.0)
        failUnlessEqual(
            'echomsg "Missing subcommand"', self.extract_command('Missing'))

    @test(testID='commands-simple-ambiguous')
    def ambiguous_simple_subcommand(self):
        """An ambigious subcommand produces an error message."""

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (':simple', 'Say hello.'),
                'helvetica': (':simple', 'Switch font.'),
                'goodbye': (':simple', 'Say goodbye.'),
            }

            def handle_hello(self, args):
                res.args = args

            def handle_helvetica(self, args):
                res.args = args

            def handle_goodbye(self, args):
                res.args = args

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None, 'he')
        yield self.delay(0.0)
        failUnlessEqual(
            '''echomsg "Ambiguous subcommand 'he': could be any of'''
            ''' hello, helvetica"''',
            self.extract_command('Ambig'))

    @test(testID='commands-unrecognised')
    def unrecognised_subcommand(self):
        """An undefined subcommand produces an error message."""

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (':simple', 'Say hello.'),
                'helvetica': (':simple', 'Switch font.'),
                'goodbye': (':simple', 'Say goodbye.'),
            }

            def handle_hello(self, args):
                res.args = args

            def handle_helvetica(self, args):
                res.args = args

            def handle_goodbye(self, args):
                res.args = args

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None, 'times')
        yield self.delay(0.0)
        failUnlessEqual(
            '''echomsg "Unrecognized subcommand 'times'"''',
            self.extract_command('Unrec'))

    @test(testID='commands-unexpected-argument')
    def unexpected_argument(self):
        """An unexpected argument produces an error message."""

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (':simple', 'Say hello.'),
            }

            def handle_hello(self, args):
                res.args = args

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None, 'hello', 'should-not-be-here')
        yield self.delay(0.0)
        failUnlessEqual(
            'Unexpected arguments: should-not-be-here', self.error_message)

    @test(testID='commands-non-simple-subcommand')
    def non_simple_subcommand(self):
        """Non-simple subcommands are supported using SubcommandHandlerBase.

        The handle_no_subcommand method is invoked when no sub-subcommand is
        provided. In this case, the subcommand can process arguments and
        options.
        """

        class HelloCommand(SubcommandHandlerBase):
            def add_arguments(self):
                self.parser.add_argument(
                    'person', default='Waldo', nargs='?', help='Who to greet.')
                self.parser.add_argument(
                    '--formal', action='store_true', help='Be formal.')

            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class GoodbyeCommand(SubcommandHandlerBase):
            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (HelloCommand, 'Say hello.'),
                'goodbye': (GoodbyeCommand, 'Say goodbye.'),
            }

        command = Command('Test')
        res = Struct()
        command.handle_main_command(
            None, 'hello', 'frank', 'should-not-be-here')
        yield self.delay(0.0)
        failUnlessEqual(
            'Unexpected arguments: should-not-be-here', self.error_message)

    @test(testID='commands-non-simple-subcommand-unexpected-args')
    def non_simple_subcommand_unexpected_args(self):
        """An unexpected argument produces an error message for subcommand."""

        class HelloCommand(SubcommandHandlerBase):
            def add_arguments(self):
                self.parser.add_argument(
                    'person', default='Waldo', nargs='?', help='Who to greet.')
                self.parser.add_argument(
                    '--formal', action='store_true', help='Be formal.')

            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class GoodbyeCommand(SubcommandHandlerBase):
            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (HelloCommand, 'Say hello.'),
                'goodbye': (GoodbyeCommand, 'Say goodbye.'),
            }

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None, 'hello', '--form')
        self.assertNoErrorMessages()
        failIf(res.args is None)
        failUnlessEqual('Waldo', res.args.person)
        failUnless(res.args.formal)

    @test(testID='commands-non-simple-help')
    def non_simple_subcommand_help(self):
        """Non-simple subcommands provide help."""

        class HelloCommand(SubcommandHandlerBase):
            def add_arguments(self):
                self.parser.add_argument(
                    'person', default='Waldo', nargs='?', help='Who to greet.')
                self.parser.add_argument(
                    '--formal', action='store_true', help='Be formal.')

            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class GoodbyeCommand(SubcommandHandlerBase):
            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (HelloCommand, 'Say hello.'),
                'goodbye': (GoodbyeCommand, 'Say goodbye.'),
            }

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None, 'hello', '--help')
        yield self.delay(0.0)
        failUnlessEqualStrings(literalText2Text('''
          | Usage: Test hello [-h] [--formal] [person]
          |
          | positional arguments:
          |   person      Who to greet.
          |
          | options:
          |   -h, --help  Show this help message.
          |   --formal    Be formal.
        '''), self.help_str)

    @test(testID='commands-sub-subcommand')
    def subcommand_with_subcommands(self):
        """Subcommands may have subcommands.

        There is no imposed limit to how deeply subcommands may nest, but VPE
        only tests to a third level (command, subcommand, sub-subcommand).

        Each level provides help.
        """

        class HiCommand(CommandHandler):
            def handle_command(self, args):
                res.command = 'hi'
                res.args = args

        class YoCommand(CommandHandler):
            def handle_command(self, args):
                res.command = 'yo'
                res.args = args

        class HelloCommand(SubcommandHandlerBase):
            def add_arguments(self):
                self.parser.add_argument(
                    'person', default='Waldo', nargs='?', help='Who to greet.')
                self.parser.add_argument(
                    '--formal', action='store_true', help='Be formal.')

            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class GreetSubcommand(SubcommandHandlerBase):
            subcommands = {
                'hi': (HiCommand, 'Informal.'),
                'yo': (YoCommand, 'Very informal.'),
            }

            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (HelloCommand, 'Say hello.'),
                'greet': (GreetSubcommand, 'Several possible greetings.'),
            }

        command = Command('Test')

        res = Struct()
        command.handle_main_command(None, 'greet', 'hi')
        self.assertNoErrorMessages()
        failIf(res.args is None)
        failUnless('hi', res.command)

        res = Struct()
        command.handle_main_command(None, 'greet', 'yo')
        self.assertNoErrorMessages()
        failIf(res.args is None)
        failUnless('yo', res.command)

        command.handle_main_command(None, '--help')
        failUnlessEqualStrings(literalText2Text('''
          | Usage: Test [-h] subcommand
          |
          | Subcommands:
          |    greet - Several possible greetings.
          |    hello - Say hello.
          | options:
          |   -h, --help  Show this help message.
        '''), self.help_str)

        command.handle_main_command(None, 'greet', '--help')
        failUnlessEqualStrings(literalText2Text('''
          | Usage: Test greet [-h] subcommand
          |
          | Subcommands:
          |    hi - Informal.
          |    yo - Very informal.
          | options:
          |   -h, --help  Show this help message.
        '''), self.help_str)

        command.handle_main_command(None, 'greet', 'yo', '--help')
        failUnlessEqualStrings(literalText2Text('''
          | Usage: Test greet yo [-h]
          |
          | options:
          |   -h, --help  Show this help message.
        '''), self.help_str)


class SimpleCommandFormation(CommandBase):
    """Formation and execution of simple commands."""
    # pylint: disable=missing-class-docstring,missing-function-docstring
    # pylint: disable=attribute-defined-outside-init

    @test(testID='commands-simple')
    def simple_command(self):
        """A simple subcommand can be created and executed."""

        class Command(SimpleCommandHandler):
            def handle_command(self, args):
                res.args = args

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None)
        failIf(res.args is None)

    @test(testID='commands-simple-options')
    def simple_command_with_options(self):
        """A simple subcommand can have options."""

        class Command(SimpleCommandHandler):
            def handle_command(self, args):
                res.args = args

            def add_arguments(self):
                self.parser.add_argument(
                    '--duck', action='store_true', help='Duck')

        res = Struct()
        command = Command('Test')

        command.handle_main_command(None)
        failIf(res.args is None)
        failIf(res.args.duck)

        command.handle_main_command(None, '--du')
        failIf(res.args is None)
        failUnless(res.args.duck)

    @test(testID='commands-simple-bad-option')
    def simple_command_bad_option(self):
        """A bad option argument produces an error message."""

        class Command(SimpleCommandHandler):
            def handle_command(self, args):
                res.args = args

            def add_arguments(self):
                self.parser.add_argument(
                    '--duck', action='store_true', help='Duck')

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None, '--swan')
        yield self.delay(0.0)
        failUnlessEqual(
            '''echomsg "Unrecognized arguments: --swan"''',
            self.extract_command('Unrec'))

    @test(testID='commands-simple-bad-argument')
    def simple_command_bad_argument(self):
        """A bad argument produces an error message."""

        class Command(SimpleCommandHandler):
            def handle_command(self, args):
                res.args = args

            def add_arguments(self):
                self.parser.add_argument(
                    '--duck', action='store_true', help='Duck')

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None, 'nothing')
        yield self.delay(0.0)
        failUnlessEqual(
            '''echomsg "Unrecognized arguments: nothing"''',
            self.extract_command('Unrec'))

    @test(testID='commands-simple-bad-pos-argument')
    def simple_command_positional_argument(self):
        """Positional arguments are supported.

        These can be given default values.
        """

        class Command(SimpleCommandHandler):
            def handle_command(self, args):
                res.args = args

            def add_arguments(self):
                self.parser.add_argument(
                    'test_name', default='everything', nargs='?',
                    help='What to test.')

        res = Struct()
        command = Command('Test')
        command.handle_main_command(None)
        self.assertNoErrorMessages()
        failIf(res.args is None)
        failUnlessEqual('everything', res.args.test_name)

        res = Struct()
        command.handle_main_command(None, 'one-thing')
        self.assertNoErrorMessages()
        failIf(res.args is None)
        failUnlessEqual('one-thing', res.args.test_name)


class CommandCompletion(CommandBase):
    """Automatic command completion support."""
    # pylint: disable=missing-class-docstring,missing-function-docstring
    # pylint: disable=attribute-defined-outside-init

    def emulate_vim_complete_call(
            self, cmdline: str, arglead: str, cursorpos: int) -> list[str]:
        """Emulate a call from Vim to generate a completion list."""
        vpe.vim.vim().vars['_vpe_args_'] = {    # pylint: disable=protected-access
            'cmdline': cmdline,
            'arglead': arglead,
            'cursorpos': cursorpos,
        }
        return VimCommandHandler.complete()

    @test(testID='commands-simple-completion')
    def simple_command_options(self):
        """Command completion of a simple command, with options."""

        class Command(SimpleCommandHandler):
            def handle_command(self, args):
                res.args = args

            def add_arguments(self):
                print("Adding arguments")
                self.parser.add_argument(
                    '--duck', action='store_true', help='Duck')
                self.parser.add_argument(
                    '--dog', action='store_true', help='Duck')

        res = Struct()
        _command = Command('Test')

        choices = self.emulate_vim_complete_call(
            cmdline='Test --du', arglead='--du', cursorpos=9)
        self.assertNoErrorMessages()
        failUnlessEqual(['--duck'], choices)

        choices = self.emulate_vim_complete_call(
            cmdline='Test ', arglead='', cursorpos=5)
        self.assertNoErrorMessages()
        failUnlessEqual(['--dog', '--duck', '--help', '-h'], choices)

        choices = self.emulate_vim_complete_call(
            cmdline='Test --', arglead='--', cursorpos=7)
        self.assertNoErrorMessages()
        failUnlessEqual(['--dog', '--duck', '--help'], choices)

        choices = self.emulate_vim_complete_call(
            cmdline='Test --d', arglead='--d', cursorpos=8)
        self.assertNoErrorMessages()
        failUnlessEqual(['--dog', '--duck'], choices)

    @test(testID='commands-subcommand-completion')
    def command_subcommand_completion(self):
        """Command completion of subcommand names."""

        class HelloCommand(SubcommandHandlerBase):
            def add_arguments(self):
                self.parser.add_argument(
                    'person', default='Waldo', nargs='?', help='Who to greet.')
                self.parser.add_argument(
                    '--formal', action='store_true', help='Be formal.')

            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class GoodbyeCommand(SubcommandHandlerBase):
            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class HeliosCommand(SubcommandHandlerBase):
            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'helios': (HeliosCommand, 'Not sure.'),
                'hello': (HelloCommand, 'Say hello.'),
                'goodbye': (GoodbyeCommand, 'Say goodbye.'),
            }

        res = Struct()
        _command = Command('Test')

        choices = self.emulate_vim_complete_call(
            cmdline='Test hell', arglead='hell', cursorpos=9)
        self.assertNoErrorMessages()
        failUnlessEqual(['hello'], choices)

        choices = self.emulate_vim_complete_call(
            cmdline='Test hel', arglead='hel', cursorpos=8)
        self.assertNoErrorMessages()
        failUnlessEqual(['helios', 'hello'], choices)

        choices = self.emulate_vim_complete_call(
            cmdline='Test ', arglead='', cursorpos=5)
        self.assertNoErrorMessages()
        failUnlessEqual(
            ['helios', 'hello', 'goodbye', '--help', '-h'], choices)

    @test(testID='commands-subcommand-option-completion')
    def command_subcommand_option_completion(self):
        """Command completion of subcommand options."""

        class HelloCommand(SubcommandHandlerBase):
            def add_arguments(self):
                self.parser.add_argument(
                    'person', default='Waldo', nargs='?', help='Who to greet.')
                self.parser.add_argument(
                    '--formal', action='store_true', help='Be formal.')

            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class GoodbyeCommand(SubcommandHandlerBase):
            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class HeliosCommand(SubcommandHandlerBase):
            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'helios': (HeliosCommand, 'Not sure.'),
                'hello': (HelloCommand, 'Say hello.'),
                'goodbye': (GoodbyeCommand, 'Say goodbye.'),
            }

        res = Struct()
        _command = Command('Test')

        choices = self.emulate_vim_complete_call(
            cmdline='Test hello ', arglead='', cursorpos=11)
        self.assertNoErrorMessages()
        failUnlessEqual(['--formal', '--help', '-h'], choices)

    @test(testID='commands-subcommand-completion-cur-bad')
    def completion_while_malformed(self):
        """Command completion handles currently malformed commands."""

        class HelloCommand(SubcommandHandlerBase):
            def add_arguments(self):
                self.parser.add_argument(
                    'person', default='Waldo', nargs='?', help='Who to greet.')
                self.parser.add_argument(
                    '--formal', action='store_true', help='Be formal.')

            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class GoodbyeCommand(SubcommandHandlerBase):
            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class HeliosCommand(SubcommandHandlerBase):
            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'helios': (HeliosCommand, 'Not sure.'),
                'hello': (HelloCommand, 'Say hello.'),
                'goodbye': (GoodbyeCommand, 'Say goodbye.'),
            }

        res = Struct()
        _command = Command('Test')

        choices = self.emulate_vim_complete_call(
            cmdline='Test fred --wi', arglead='', cursorpos=14)
        self.assertNoErrorMessages()
        failUnlessEqual([], choices)

    @test(testID='complete-sub-subcommand')
    def complete_sub_subcommand(self):
        """Subcommands of subcommands can be completed."""

        class HiCommand(CommandHandler):
            def handle_command(self, args):
                res.command = 'hi'
                res.args = args

        class YoCommand(CommandHandler):
            def handle_command(self, args):
                res.command = 'yo'
                res.args = args

        class HelloCommand(SubcommandHandlerBase):
            def add_arguments(self):
                self.parser.add_argument(
                    'person', default='Waldo', nargs='?', help='Who to greet.')
                self.parser.add_argument(
                    '--formal', action='store_true', help='Be formal.')

            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class GreetSubcommand(SubcommandHandlerBase):
            subcommands = {
                'hi': (HiCommand, 'Informal.'),
                'yo': (YoCommand, 'Very informal.'),
            }

            def handle_no_subcommand(self, cmd_info, args):
                res.args = args

        class Command(TopLevelSubcommandHandler):
            subcommands = {
                'hello': (HelloCommand, 'Say hello.'),
                'greet': (GreetSubcommand, 'Several possible greetings.'),
            }

        res = Struct()
        _command = Command('Test')

        choices = self.emulate_vim_complete_call(
            cmdline='Test gre y', arglead='', cursorpos=10)
        self.assertNoErrorMessages()
        failUnlessEqual(['yo'], choices)

        choices = self.emulate_vim_complete_call(
            cmdline='Te gre ', arglead='', cursorpos=9)
        self.assertNoErrorMessages()
        failUnlessEqual(['hi', 'yo', '--help', '-h'], choices)

    @test(testID='complete-unknown-command')
    def complete_unkown_command(self):
        """An unkonwn command results in no completions."""

        choices = self.emulate_vim_complete_call(
            cmdline='Wibble ', arglead='', cursorpos=7)
        self.assertNoErrorMessages()
        failUnlessEqual([], choices)
