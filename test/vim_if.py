"""Interface to Vim for testing."""
from __future__ import annotations

import os
import pathlib
import platform
import re
import subprocess
import time

SESSION = 'TEST'
R_PATCH = re.compile(r'patch-(\d+)\.(\d+)\.(\d+)')


def get_tmp_paths(filename: str) -> Tuple[pathlib.Path, pathlib.Path]:
    """Get temporary path names for test and Vim worlds."""
    vim_path = test_path = pathlib.Path(f'/tmp/{filename}')
    if platform.platform().startswith('CYGWIN'):
        vim_path = pathlib.Path(f'$TEMP/{filename}')
    return test_path, vim_path


PY_NAME = 'test.py'


def eval_call(expr):
    """Quote and escape a Vim expression.

    :expr: The Vim expression.
    """
    expr = expr.replace("'", "''")
    return f"eval('{expr}')"


def vim_single_quote(expr):
    """Put expression in single quotes, using Vim escaping rules.

    :expr: The Vim expression.
    """
    expr = expr.replace("'", "''")
    return f"'{expr}'"


def double_quote(expr):
    """Put expression in double quotes, using Python escaping rules.

    :expr: The Vim expression.
    """
    expr = expr.replace('"', r'\"')
    return f'"{expr}"'


def single_quote(expr):
    """Put expression in single quotes, using Python escaping rules.

    :expr: The Vim expression.
    """
    expr = expr.replace("'", r"\'")
    return f"'{expr}'"


class VimSession:
    version_str = ''
    version = []

    def __init__(self):
        self.proc = None
        self.execute_vim('qa!')
        self.get_version()
        self.proc = None
        self.ensure_vim_session()

    def execute_vim(self, cmd):
        expr = f"execute({vim_single_quote(cmd)})"
        ret = self.eval_vim(expr)
        return ret

    def feedkeys(self, keys: str):
        """Feed keys to the Vim server.

        This used the feedkeys function because we want key mapping to occur.
        Double quotes are wrapped around the *keys* string so that special
        keypresses can be easily emulated. For example:<py>:

            # Emulate pressing the F4 key.
            feedkeys(r'\<F4>')

        :keys: A string of the keys to feed.
        """
        expr = f"feedkeys({double_quote(cmd)})"
        ret = self.eval_vim(expr)
        return ret

    @staticmethod
    def eval_vim(expr):
        cproc = subprocess.run(
            ['vim', '--servername', SESSION, '--remote-expr', eval_call(expr)],
            capture_output=True)
        if cproc.returncode != 0:
            return None
        return cproc.stdout.strip().decode()

    @classmethod
    def has_patch(cls, patch_name):
        m = R_PATCH.match(patch_name)
        p_ver = [int(v, 10) for v in m.groups()]
        return p_ver <= cls.get_version()

    @classmethod
    def get_version(cls):
        if not cls.version_str:
            cproc = subprocess.run(['vim', '--version'], capture_output=True)
            lines = cproc.stdout.strip().decode().splitlines()
            cls.version_str = lines[0].split()[4]
            cls.version = [int(p) for p in cls.version_str.split('.')[:2]]
            cls.version.append(int(lines[1].split()[-1].split('-')[-1], 10))
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
            self.proc = subprocess.Popen(cmd, stderr=subprocess.DEVNULL)

            # Make sure Vim is running and responsive.
            while self.eval_vim('1') != '1':
                time.sleep(0.1)

            # Set tge window to a fixed size and position. Ensure swap files
            # are neatly tucked away.
            self.execute_vim('let &guifont = "Monospace 8"')
            self.execute_vim('set columns=100')
            self.execute_vim('set lines=60')
            self.execute_vim('winpos 0 0')
            self.execute_vim('set directory=./test-swap//')

            # Switch back to the nominated Vim window, if defined.
            edvim = os.environ.get('EDVIM', '')
            if edvim:
                subprocess.run(
                    ['vim', '--servername', edvim, '--remote-expr',
                     'foreground()'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def execute_string(self, text):
        """Execute a Python statement supplied as a string.

        :text: The Python statement to execute.
        """
        return self.execute_vim(f'py3 {text}')

    def execute(self, text, py_name=None):
        py_path, vim_path = get_tmp_paths(py_name or PY_NAME)
        with open(py_path, 'wt') as f:
            f.write(text)
            f.write('\n')
        return self.execute_vim(f'py3file {str(vim_path)}')

    def py_eval(self, expr):
        """Remotely run python using py3eval.

        :expr: The Python expression to evaluate.
        """
        eval_expr = f'py3eval({vim_single_quote(expr)})'
        return self.eval_vim(eval_expr)
