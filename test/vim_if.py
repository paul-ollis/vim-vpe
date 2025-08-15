"""Interface to Vim for testing."""
from __future__ import annotations

import functools
import inspect
import os
import pathlib
import platform
import re
import subprocess
import time
from pathlib import Path

from cleversheep3.Test.Tester import fail

SESSION = 'TEST'
r_patch = re.compile(r'patch-(\d+)\.(\d+)\.(\d+)')
r_tb_file_line = re.compile(r'  File "(?P<file>[^"]+)", line (?P<line>[0-9]+)')

open_text_for_write = functools.partial(open, mode='wt', encoding='utf-8')


def get_tmp_paths(filename: str) -> tuple[Path, Path]:
    """Get temporary path names for test and Vim worlds."""
    vim_path = test_path = pathlib.Path(f'/tmp/{filename}')
    if platform.platform().startswith('CYGWIN'):
        # On windows, use a literal $TEMP here. Vim will expand it correctly.
        vim_path = pathlib.Path(f'$TEMP/{filename}')
    return test_path, vim_path


PY_NAME = 'test.py'


def format_vim_eval_call(expr):
    """Quote and escape a Vim expression.

    :expr: The Vim expression.
    """
    expr = expr.replace("'", "''")
    return f"eval('{expr}')"


def single_quote_for_vim(expr):
    """Put expression in single quotes, using Vim escaping rules.

    :expr: The Vim expression.
    """
    expr = expr.replace("'", "''")
    return f"'{expr}'"


def double_quote_for_python(expr):
    """Put expression in double quotes, using Python escaping rules.

    :expr: The Vim expression.
    """
    expr = expr.replace('"', r'\"')
    return f'"{expr}"'


class VimSession:
    """An object managing a graphical Vim session."""
    version_str = ''
    version = []

    test_execution_wrapper_filename = 'test_execution_wrapper.py'
    test_errors_filename = 'test_errors.txt'

    def __init__(self):
        self.proc = None
        self.execute_vim_command('qa!')
        self.get_version()
        self.ensure_vim_session()

    @property
    def test_execution_wrapper_path(self) -> Path:
        """The script execution path, as seen by test script code."""
        test_path, _ = get_tmp_paths(self.test_execution_wrapper_filename)
        return test_path

    @property
    def vim_execution_wrapper_path(self) -> Path:
        """The script execution path, as seen by test script code."""
        _, vim_path = get_tmp_paths(self.test_execution_wrapper_filename)
        return vim_path

    @property
    def test_error_path(self) -> Path:
        """The error text path, as seen by code in the Vim session."""
        test_path, _= get_tmp_paths(self.test_errors_filename)
        return test_path

    @property
    def vim_error_path(self) -> Path:
        """The error text path, as seen by code in the Vim session."""
        _, vim_path = get_tmp_paths(self.test_errors_filename)
        return vim_path

    def create_script_execution_wrapper(self, script_path: str) -> str:
        """Create a wrapper script to execute another script.

        The created tries to execute the wrapped script and handles any
        exception, by writing a traceback to the error file.

        :script_path: The path of the script to wrap.
        :return:      The Vim world name of the created file.
        """
        template = inspect.cleandoc(r'''# Execute a file.
        from pathlib import Path

        err_path = Path('{error_file_path}')
        err_path.unlink(missing_ok=True)

        with open('{script_path}', mode='rt', encoding='utf-8') as f:
            source_code = f.read()
        try:
            code = compile(source_code, '{script_path}', 'exec')
            exec(code)
        except Exception as e:
            import traceback
            with err_path.open(mode='wt', encoding='utf-8') as f:
                traceback.print_exception(e, file=f)
                f.flush()
        ''')
        code = template.format(
            script_path=script_path, error_file_path=self.vim_error_path)
        with open_text_for_write(self.test_execution_wrapper_path) as f:
            f.write(code)
        return self.vim_execution_wrapper_path

    def execute_vim_command(self, cmd):
        """Execute a Vim command within the managed Vim editor."""
        expr = f"execute({single_quote_for_vim(cmd)})"
        ret = self.eval_vim(expr)
        return ret

    def execute_vim_py3file_script(self, cmd, adjust):
        """Execute a Vim command which is invoked by py3file."""
        test_errors_path = self.test_error_path
        expr = f"execute({single_quote_for_vim(cmd)})"
        ret = self.eval_vim(expr)
        if test_errors_path.exists():
            text = test_errors_path.read_text(encoding='utf-8').strip()
            if text:
                fail(self._massage_traceback(text, adjust))

        return ret

    @staticmethod
    def _massage_traceback(
            text: str, adjust: None | tuple[str, int, Path],
        ) -> str:
        """Massage a traceback prodiced within Vim to be more meaningful."""
        newlines = []
        mode = ''
        for line in text.splitlines():
            if line.startswith('    code = compile(source_code, '):
                mode = 'drop-compile'
                newlines.pop()
                continue
            m = r_tb_file_line.match(line)
            if m and adjust:
                to_name, offset, from_path = adjust
                file = m.group('file')
                if file == str(from_path):
                    n = int(m.group('line')) + offset
                    line = f'  File "{to_name}", line {n - 1}'
                mode = ''
            if not mode:
                newlines.append(line)
        return '\n'.join(newlines)

    def feedkeys(self, keys: str):
        """Feed keys to the Vim server.

        This used the feedkeys function because we want key mapping to occur.
        Double quotes are wrapped around the *keys* string so that special
        keypresses can be easily emulated. For example:<py>:

            # Emulate pressing the F4 key.
            feedkeys(r'\<F4>')

        :keys: A string of the keys to feed.
        """
        expr = f"feedkeys({double_quote_for_python(cmd)})"
        ret = self.eval_vim(expr)
        return ret

    @staticmethod
    def eval_vim(expr):
        cproc = subprocess.run(
            [
                'vim', '--servername', SESSION, '--remote-expr',
                format_vim_eval_call(expr),
            ],
            capture_output=True)
        if cproc.returncode != 0:
            return None
        return cproc.stdout.strip().decode()

    @classmethod
    def has_patch(cls, patch_name):
        m = r_patch.match(patch_name)
        p_ver = [int(v, 10) for v in m.groups()]
        return p_ver <= cls.get_version()

    @classmethod
    def get_version(cls):
        if not cls.version_str:
            cproc = subprocess.run(['vim', '--version'], capture_output=True)
            lines = cproc.stdout.strip().decode().splitlines()
            cls.version_str = lines[0].split()[4]
            cls.version = [int(p) for p in cls.version_str.split('.')[:2]]
            if lines[1].startswith('Included patches: '):
                cls.version.append(int(lines[1].split()[-1].split('-')[-1], 10))
            else:
                cls.version.append(0)
        return cls.version

    def ensure_vim_session(self):
        """Ensure that the required Vim session is running.

        If the session is not already running then a new one is started with
        the following characteristics.

        - Its servermname is 'TEST'.
        - The environment variable VPE_TEST_MODE is set to '1'.
        - The session is run without plugins.
        - The '-f' option is used to prevent Vim from daemonising.
        - The GUI version of vim is executed.
        - Errors are rdeirected to /dev/null or its equivalent.
        - The :vim:`directory` option is set to './test-swap//' so that
          swap files can be easily cleaned up.

        This method waits until the new Vim session appears to be responsive,
        using the `vim_eval` method.

        For consistency, the font, window position and size are set to fixed
        values.

        If the EDIVIM environment variable is set, this method will attempt to
        switch keyboard and mouse focus back to the $EDVIM Vim session.
        """
        ret = self.eval_vim('0')
        if ret != '0':
            os.environ['VPE_TEST_MODE'] = '1'
            cmd = [
                'xterm','-e',
                'gdb', '-ex', 'run', '--args',
                '/home/paul/develop/tracking/vim/vim/src/vim', '-g',
                '-f', '--noplugin',
                '--servername', SESSION]
            cmd = [
                '/home/paul/develop/tracking/vim/vim/src/vim', '-g',
                '--noplugin', '--servername', SESSION]
            cmd = ['gvim', '--noplugin', '--servername', SESSION]
            # pylint: disable=consider-using-with
            self.proc = subprocess.Popen(cmd, stderr=subprocess.DEVNULL)

            # Make sure Vim is running and responsive.
            while self.eval_vim('1') != '1':
                time.sleep(0.1)

            # Set the window to a fixed size and position. Ensure swap files
            # are neatly tucked away.
            self.execute_vim_command('let &guifont = "Monospace 8"')
            self.execute_vim_command('set columns=100')
            self.execute_vim_command('set lines=60')
            self.execute_vim_command('winpos 0 0')
            self.execute_vim_command('set directory=./test-swap//')

            # Switch back to the nominated Vim window, if defined.
            edvim = os.environ.get('EDVIM', '')
            if edvim:
                subprocess.run(
                    ['vim', '--servername', edvim, '--remote-expr',
                     'foreground()'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    check=False)

    def execute_python_code(self, code: str, py_name=None, adjust=None):
        """Execute a Python script."""
        test_path, vim_path = get_tmp_paths(py_name or PY_NAME)
        with open(test_path, 'wt', encoding='utf-8') as f:
            f.write(code)
        wrapper_path = self.create_script_execution_wrapper(vim_path)
        if adjust:
            adjust = adjust + (vim_path,)
        return self.execute_vim_py3file_script(
            f'py3file {str(wrapper_path)}', adjust=adjust)

    def py_eval(self, expr):
        """Remotely run python using py3eval.

        :expr: The Python expression to evaluate.
        """
        eval_expr = f'py3eval({single_quote_for_vim(expr)})'
        return self.eval_vim(eval_expr)
