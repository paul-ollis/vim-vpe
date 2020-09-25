"""Common test support."""

import inspect
import itertools
import pathlib
import pickle

from typing import ClassVar, Optional, Callable, Iterator

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *

# Some explicit imports to make mypy happy.
from cleversheep3.Test.Tester import fail, Suite

import vim_if

import vpe


def clean_code_block(code):
    """Clean up the lines in a docstring code block.

    - Any leading '<code>' line is removed.
    - All lines are dedented and stripped of trailing whitespace.
    - Leading and trailing blank lines are removed.

    :code: The test of the code block.
    """
    lines = code.splitlines()
    if lines[0].strip() == '<code>':
        lines.pop(0)
    ind = min(len(line) - len(line.lstrip()) for line in lines if line.strip())
    lines = [line[ind:].rstrip() for line in lines]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines)


class CodeSource:
    """Mix-in for tests that use code embeded in docstrings."""
    vs = None

    def suiteSetUp(self):
        """called to set up the suite."""
        self.init()

    def init(self):
        r"""called to set up the suite.

        :<py>:

            import functools
            import os
            import pickle
            import sys

            sys.path.append(os.getcwd())

            import vim as _vim

            from vpe.wrappers import Struct

            from vpe import vim
            import vpe

            vim.current.buffer.name = '/tmp/test.txt'

            try:
                bufadd = vim.bufadd
            except AttributeError:
                def bufadd(name):
                    vim.command(f'enew')
                    vim.current.buffer.name = name

            # Remove all but the first buffer.
            def zap_bufs():
                numbers = [buf.number for buf in vim.buffers]
                for n in numbers[1:]:
                    vpe.commands.bwipeout(n)

            # Switch the current buffer to another.
            def get_alt_buffer():
                if len(vim.buffers) < 2:
                    bufadd('two')
                n = vim.current.buffer.number
                for b in vim.buffers:
                    if b.number != n:
                        _vim.command(f'b {b.number}')
                        # _vim.current.buffer = b
                        return b

            # Dump the pickle of an object to file.
            def dump(obj):
                with open('/tmp/vpe-test-dump.bin', 'wb') as f:
                    try:
                        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
                    except exception as e:
                        f.write(
                            f'pickle dump failed for {repr(obj)}\n'.encode())
                        f.write(f'reason: {e}\n'.encode())
        """
        if CodeSource.vs is None:
            CodeSource.vs = vim_if.VimSession()
            self.vs.execute(self.mycode())

    def vim_cov_start(self):
        r"""Start coverage without previous accumulated data.

        :<py>:

            import coverage

            cov = coverage.Coverage(
                data_file='.coverage.vim')
            cov.start()
        """
        self.run_self(py_path='/tmp/cov_script.py')

    def vim_cov_continue(self):
        r"""Continue coverage, using previously accumulated data.

        :<py>:

            import coverage
            cov = coverage.Coverage(data_file='.coverage.vim', auto_data=True)
            cov.start()
        """
        self.run_self(py_path='/tmp/cov_script.py')

    def vim_cov_stop(self):
        r"""Stop coverage and save the data.

        :<py>:

            cov.stop()
            cov.save()
        """
        self.run_self(py_path='/tmp/cov_script.py')

    @staticmethod
    def extract_code(doc: str) -> Optional[str]:
        """Extract the code from a docstring.

        :doc: The doc string.
        """
        lines = doc.splitlines()
        for i, line in enumerate(lines):
            if line.strip().endswith(':<py>:'):
                return clean_code_block('\n'.join(lines[i + 1:]))
        return None

    @staticmethod
    def extract_vim_code(doc: str) -> Optional[str]:
        """Extract Vim code from a docstring.

        :doc: The doc string.
        """
        lines = doc.splitlines()
        for i, line in enumerate(lines):
            if line.strip().endswith(':<vim>:'):
                return clean_code_block('\n'.join(lines[i + 1:]))
        return None

    def _mycode(
            self, extract_code: Callable, stack_level: int = 1) -> str:
        """Extract a block of code from the caller's docstring."""
        stack = inspect.stack()
        method_name = stack[stack_level].function
        for cls in self.__class__.__mro__:
            method = cls.__dict__.get(method_name, None)
            if method is not None:
                code = extract_code(getattr(method, '__doc__', ''))
                if code is not None:
                    return code

        fail('code not found in docstring of:'
             f' {self.__class__.__name__}.{method_name}')
        return ''

    def mycode(self, stack_level: int = 1) -> str:
        """Extract a block of Python code from the caller's docstring."""
        return self._mycode(self.extract_code, stack_level=stack_level + 1)

    def myvimcode(self, stack_level: int = 1) -> str:
        """Extract a block of Vim code from the caller's docstring."""
        return self._mycode(self.extract_vim_code, stack_level=stack_level + 1)

    @staticmethod
    def result():
        """Get the result from a remote Vim execution."""
        with open('/tmp/vpe-test-dump.bin', 'rb') as f:
            data = f.read()
        try:
            v = pickle.loads(data)
        except Exception as e:  # pylint: disable=broad-except
            log.error(f'Pickle load failed@ {e}')
            log.error(f'Pickle data: {data!r}')
            return None
        return v

    def run_self(self, py_path=None):
        """Run the Python code in the caller's docstring."""
        self.vs.execute(self.mycode(stack_level=2), py_path=py_path)
        return self.result()

    def eval(self, expr):
        """Evaluate an expression in the Vim world and return the result.

        :<py>:

            dump({expr})
        """
        self.vs.execute(self.mycode().format(expr=expr))
        return self.result()


class Base(Suite, CodeSource):
    """Base for Vim tests."""
    cov_running: ClassVar[bool] = False
    vim: vpe.Vim
    vim_options: vpe.wrappers.Options

    def suiteSetUp(self):
        """called to set up the suite."""
        super().suiteSetUp()
        CodeSource.suiteSetUp(self)
        self.vim = self.eval('vim')
        self.vim_options = vpe.vim.options
        if Base.cov_running:
            self.vim_cov_continue()
        else:
            self.vim_cov_start()
            Base.cov_running = True

    def suiteTearDown(self):
        self.vim_cov_stop()
        super().suiteTearDown()

    def setUp(self):
        pathlib.Path('/tmp/test.py').unlink(missing_ok=True)


class CommandsBase(Base):
    """Base for tests that anallyse capture command execution."""
    saved_id_source: Iterator[int]

    def suiteSetUp(self):
        """Suite init function."""
        super().suiteSetUp()
        vpe.vim.vim().register_command_callback(self.on_command)

    def suiteTearDown(self):
        """Suite clean up function."""
        super().suiteTearDown()
        vpe.vim.vim().register_command_callback(None)
        vpe.core.id_source = self.saved_id_source

    def setUp(self):
        """Per test init function."""
        self.commands = []
        self.saved_id_source = vpe.core.id_source
        vpe.core.id_source = itertools.count(100)

    def tearDown(self):
        """Per test clean up."""
        vpe.core.id_source = self.saved_id_source

    def on_command(self, cmd: str):
        """Callback for when vim.command is invoked.

        :cmd: The command that was run.
        """
        self.commands.append(cmd)
        print(cmd)

    def check_commands(self):
        """Check the set of issued Vim commands."""
        code = self.myvimcode(stack_level=2)
        e_lines = code.splitlines()
        a_lines = self.commands
        for i, (expected, actual) in enumerate(zip(e_lines, a_lines)):
            failUnlessEqual(expected, actual, add_message=f'Index {i}')
        if len(a_lines) > len(e_lines):
            for i, line in enumerate(a_lines[len(e_lines):]):
                print(f'Extra line {i + len(e_lines)}: {line}')
        failUnlessEqual(len(e_lines), len(a_lines))
