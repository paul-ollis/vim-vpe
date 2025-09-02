"""Common test support."""

import inspect
import itertools
import os
import pathlib
import pickle
import platform

from typing import Callable, ClassVar, Iterator, Optional

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *

# Some explicit imports to make mypy happy.
from cleversheep3.Test.Tester import Suite, fail

import vim_if

import vpe

OBJ_DUMP_NAME = 'vpe-test-dump.bin'
COV_START_SCRIPT_NAME = 'cov_start_script.py'
COV_STOP_SCRIPT_NAME = 'cov_stop_script.py'
COV_CONT_SCRIPT_NAME = 'cov_cont_script.py'

# pylint: disable=deprecated-method

def fix_path(path: str) -> str:
    """Convert a Windows path to an equivalent Linux style one.

    This removes any driver letter and converts the back to forward slashes.
    This is used to check actual to expected file names.
    """
    if path[1:2] == ':':
        path = path[2:]
    return path.replace('\\', '/')


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
    cov_started: ClassVar[bool] = False
    cov_running: ClassVar[bool] = False

    def suiteSetUp(self):
        """called to set up the suite."""
        self.init()

    def init(self):
        r"""Called to set up the suite.

        The first time this is invoked, it makes sure that the test Vim session
        is started and initialised with the VPE library and any supporting
        code.

        :<py>:

            import functools
            import os
            import pathlib
            import pickle
            import platform
            import sys
            from pathlib import Path

            here = Path.cwd().resolve()
            sys.path.append(str(here.parent))  # For import of vpe.
            sys.path.append(str(here))         # For import of support code.

            import vim as _vim

            import vpe
            from vpe import vim
            from vpe.wrappers import Struct

            # Redirect logging and use a largish buffer for ease of debugging.
            log_mode = os.environ.get('VPE_LOGGING', '')
            if log_mode == '':
                vpe.log.redirect()
            elif log_mode != 'tty':
                f = open(log_mode, 'at', buffering=1)
                sys.stdout = sys.stderr = f
            vpe.log.set_maxlen(3000)

            # Create a temp path name.
            def tmp_path(stem):
                dirname = os.environ.get('TEMP', '/tmp')
                return f'{dirname}/{stem}'

            # Give the initial buffer a suitable name.
            vim.current.buffer.name = tmp_path('test.txt')

            try:
                bufadd = vim.bufadd
            except AttributeError:
                def bufadd(name):
                    vim.command(f'enew')
                    vim.current.buffer.name = name

            # Generate display buffer name.
            def get_disp_name(name):
                if platform.system() == 'Windows':
                    return rf'C:\[[{name}]]'
                return f'/[[{name}]]'

            # Remove all but the first buffer.
            def zap_bufs():
                with vpe.temp_log(tmp_path('test_zap.log')):
                    for b in vim.buffers:
                        b.options.modified = False
                    vpe.commands.buffer(1)
                    vpe.commands.tabonly()
                    vpe.commands.wincmd('o')
                    print("N-tabs", len(vim.tabpages))
                    print("N-wins", len(vim.windows))
                    print("N-bufs", len(vim.buffers))
                    numbers = [buf.number for buf in vim.buffers]
                    for n in numbers[1:]:
                        vpe.commands.bwipeout(n)
                    print("N-bufs", len(vim.buffers))

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
                with open(DUMP_PATH, 'wb') as f:
                    try:
                        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
                    except exception as e:
                        f.write(
                            f'pickle dump failed for {repr(obj)}\n'.encode())
                        f.write(f'reason: {e}\n'.encode())

            vim.command('nmap <S-F1> :py3 vpe.log.show()<CR>')
        """
        if CodeSource.vs is None:
            print("Start Vim Session")
            CodeSource.vs = vim_if.VimSession()
            self.vs.execute_python_code('import os')
            if platform.platform().startswith('CYGWIN'):
                self.vs.execute_python_code(
                    f'DUMP_PATH = os.environ["TEMP"] + "/{OBJ_DUMP_NAME}"')
            else:
                self.vs.execute_python_code(
                    f'DUMP_PATH = "/tmp/{OBJ_DUMP_NAME}"')
            self.vim_cov_start()
            source_code, _adjust = self.mycode()
            self.vs.execute_python_code(source_code, py_name='init.py')

    def stop_vim_session(self):
        """Stop the running Vim session."""
        if CodeSource.vs is not None:
            self.vim_cov_stop()
            CodeSource.vs.execute_vim_command('qa!')
            CodeSource.vs = None

    def vim_cov_start(self):
        r"""Start (or continue) coverage."""
        if CodeSource.cov_started:
            self._vim_cov_continue()
        else:
            self._vim_cov_start()
            CodeSource.cov_started = True

    def _vim_cov_start(self):
        r"""Start coverage without previous accumulated data.

        :<py>:

            import platform
            import vim as _vim

            if int(_vim.vvars['version']) >= 802:
                import coverage

                if platform.system() == 'Windows':
                    cov = coverage.Coverage(data_file='.coverage-win.vim')
                else:
                    cov = coverage.Coverage(data_file='.coverage.vim')
                cov.start()
        """
        if not CodeSource.cov_running:
            self.run_self(py_name=COV_START_SCRIPT_NAME)
            CodeSource.cov_running = True

    def _vim_cov_continue(self):
        r"""Continue coverage, using previously accumulated data.

        :<py>:

            import platform
            import vim as _vim

            if int(_vim.vvars['version']) >= 802:
                import coverage

                if platform.system() == 'Windows':
                    cov = coverage.Coverage(
                        data_file='.coverage-win.vim', auto_data=True)
                else:
                    cov = coverage.Coverage(
                        data_file='.coverage.vim', auto_data=True)
                cov.start()
        """
        if not CodeSource.cov_running:
            self.run_self(py_name=COV_CONT_SCRIPT_NAME)
            CodeSource.cov_running = True

    def vim_cov_stop(self):
        r"""Stop coverage and save the data.

        :<py>:

            import vim as _vim

            if int(_vim.vvars['version']) >= 802:
                try:
                    cov.stop()
                    cov.save()
                except Exception as e:
                    pass #  Occurs when Vim gets restarted.
        """
        if CodeSource.cov_running:
            self.run_self(py_name=COV_STOP_SCRIPT_NAME)
            CodeSource.cov_running = False

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
    def _find_py_code_offset(lines: list[str]) -> int:
        start = -1
        for i, line in enumerate(lines):
            if line.strip().endswith(':<py>:'):
                start = i
                continue
            if start >= 0 and line.strip():
                return i
        return -1

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
            self, extract_code: Callable, stack_level: int = 1,
            fields: dict | None = None,
        ) -> tuple[str, tuple[str, int]]:
        """Extract a block of code from the caller's docstring.

        :return:
            A tuple of the extracted code and traceback adjustment information.
            The adjustment information is a either an empty tuple or a 2-tuple
            of the filename from which the code was extracted and the line
            where the extracted code started.
        """
        stack = inspect.stack()
        method_name = stack[stack_level].function
        adjust_info = ()
        for cls in self.__class__.__mro__:
            method = cls.__dict__.get(method_name, None)
            if method is not None:
                try:
                    lines, lnum = inspect.getsourcelines(method)
                    sourcefile = inspect.getsourcefile(method)
                except TypeError:
                    adjust_info = ()
                else:
                    offset = self._find_py_code_offset(lines)
                    adjust_info = (sourcefile, offset + lnum)

                code = extract_code(getattr(method, '__doc__', ''))
                if code is not None:
                    if fields:
                        return code.format(**fields), adjust_info
                    else:
                        return code, adjust_info

        fail('code not found in docstring of:'
             f' {self.__class__.__name__}.{method_name}')
        return '', ()

    def mycode(
            self, stack_level: int = 1, **kwargs,
        ) -> tuple[str, tuple[str, int]]:
        """Extract a block of Python code from the caller's docstring."""
        return self._mycode(
            self.extract_code, stack_level=stack_level + 1, fields=kwargs)

    def myvimcode(
             self, stack_level: int = 1) -> tuple[str, tuple[str, int]]:
        """Extract a block of Vim code from the caller's docstring."""
        return self._mycode(
            self.extract_vim_code, stack_level=stack_level + 1)

    @staticmethod
    def result():
        """Get the result from a remote Vim execution."""
        obj_dump_path, _ = vim_if.get_tmp_paths(OBJ_DUMP_NAME)
        if not obj_dump_path.exists():
            return None
        with open(obj_dump_path, 'rb') as f:
            data = f.read()
        try:
            v = pickle.loads(data)
        except Exception as e:  # pylint: disable=broad-except
            log.error(f'Pickle load failed@ {e}')
            log.error(f'Pickle data: {data!r}')
            return None
        return v

    def run_self(self, py_name=None, stack_level=2, **kwargs):
        """Run the Python code in the caller's docstring."""
        obj_dump_path, _ = vim_if.get_tmp_paths(OBJ_DUMP_NAME)
        if obj_dump_path.exists():
            os.unlink(obj_dump_path)
        source_code, adjust = self.mycode(stack_level=stack_level, **kwargs)
        self.vs.execute_python_code(
            source_code, py_name=py_name, adjust=adjust)
        result = self.result()
        return result

    def run_suite_setup(self):
        """Run a suite set up script."""
        return self.run_self(py_name='suite_setup.py', stack_level=3)

    def run_setup(self):
        """Run a set up script."""
        return self.run_self(py_name='setup.py', stack_level=3)

    def run_suite_teardown(self):
        """Run a suite tear down script."""
        return self.run_self(py_name='suite_teardown.py', stack_level=3)

    def run_teardown(self):
        """Run a tear down script."""
        return self.run_self(py_name='teardown.py', stack_level=3)

    def run_continue(self):
        """Run a continue script."""
        return self.run_self(py_name='continue.py', stack_level=3)

    def eval(self, expr):
        """Evaluate an expression in the Vim world and return the result.

        :<py>:

            dump({expr})
        """
        source_code, _adjust = self.mycode()
        self.vs.execute_python_code(source_code.format(expr=expr))
        return self.result()


class Base(Suite, CodeSource):
    """Base for Vim tests."""
    vim: vpe.Vim
    vim_options: vpe.wrappers.Options

    def suiteSetUp(self):
        """called to set up the suite."""
        super().suiteSetUp()
        CodeSource.suiteSetUp(self)
        self.vim = self.eval('vim')
        self.vim_options = vpe.vim.options
        self.vim_cov_start()

    def suiteTearDown(self):
        self.vim_cov_stop()
        super().suiteTearDown()

    def setUp(self):
        pathlib.Path('/tmp/test.py').unlink(missing_ok=True)


class CommandsBase(Base):
    """Base for tests that analyse captured command execution."""
    saved_id_source: Iterator[int]

    def suiteSetUp(self):
        """Suite init function."""
        super().suiteSetUp()
        vpe.vim.vim().register_command_callback(self.on_command)

    def suiteTearDown(self):
        """Suite clean up function."""
        super().suiteTearDown()
        vpe.vim.vim().register_command_callback(None)
        #vpe.common.id_source = self.saved_id_source

    def setUp(self):
        """Per test init function."""
        self.commands = []
        self.saved_id_source = vpe.common.id_source
        #vpe.common.id_source = itertools.count(100)

    def tearDown(self):
        """Per test clean up."""
        #vpe.common.id_source = self.saved_id_source

    def on_command(self, cmd: str):
        """Callback for when vim.command is invoked.

        :cmd: The command that was run.
        """
        self.commands.append(cmd)
        print(cmd)

    def check_commands(self, **values):
        """Check the set of issued Vim commands.

        :values:
            A set of keyword arguments used to parameterise the expected
            command output.
        """
        code, _ = self.myvimcode(stack_level=2)
        code = code.format(**values)
        e_lines = code.splitlines()
        a_lines = self.commands
        if e_lines == ['<NOP>']:
            failUnlessEqual(0, len(a_lines))
        else:
            for i, (expected, actual) in enumerate(zip(e_lines, a_lines)):
                failUnlessEqual(expected, actual, add_message=f'Index {i}')
            if len(a_lines) > len(e_lines):
                for i, line in enumerate(a_lines[len(e_lines):]):
                    print(f'Extra line {i + len(e_lines)}: {line}')
            failUnlessEqual(len(e_lines), len(a_lines))
