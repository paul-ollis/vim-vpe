"""Function style execution of vim commands."""
# pylint: disable=deprecated-method

# pylint: disable=unused-wildcard-import,wildcard-import
from CleverSheep.Test.Tester import *
from CleverSheep.Test.Tester import test, runModule

import support

import vpe

_run_after = ['test_vim.py']


class Commands(support.Base):
    """VPE support for exeuting commands using functions calls.

    The vpe.commands module provide function equivalents for most Ex commands.
    """
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

            dump(res)
        """
        res = self.run_self()
        failUnless(isinstance(res.v, AttributeError))


if __name__ == '__main__':
    runModule()
