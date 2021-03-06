"""Interface to Vim for testing."""
from __future__ import annotations

import os
import pathlib
import subprocess

SESSION = 'TEST'
PY_PATH = pathlib.Path('/tmp/test.py')


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
    def get_version(cls):
        if not cls.version_str:
            cproc = subprocess.run(['vim', '--version'], capture_output=True)
            lines = cproc.stdout.strip().decode().splitlines()
            cls.version_str = lines[0].split()[4]
            cls.version = [int(p) for p in cls.version_str.split('.')[:2]]
        return cls.version

    def ensure_vim_session(self):
        ret = self.eval_vim('0')
        if ret != '0':
            subprocess.run(
                ['gvim', '--noplugin', '--servername', 'TEST',
                 '-geometry', '80x60+0+0'],
                stderr=subprocess.DEVNULL)

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

    def execute(self, text, py_path=None):
        py_path = py_path or PY_PATH
        with open(py_path, 'wt') as f:
            f.write(text)
            f.write('\n')
        return self.execute_vim(f'py3file {str(py_path)}')

    def py_eval(self, expr):
        """Remotely run python using py3eval.

        :expr: The Python expression to evaluate.
        """
        eval_expr = f'py3eval({vim_single_quote(expr)})'
        return self.eval_vim(eval_expr)


# TODO: Defunct, but keeping around in case the idea proves useful.
class OptionsProxy:
    def __init__(self, vs):
        self.__dict__['_vs'] = vs

    def __getitem__(self, name):
        """Get an option's value using dict style access.

        :<py>:

            dump(vim.options['{name}'])
        """
        self._vs.execute(self.mycode().format(name=name))
        return self.result()

    def __getattr__(self, name):
        """Get an option's value using attr style access.

        :<py>:

            dump(vim.options.{name})
        """
        self._vs.execute(self.mycode().format(name=name))
        return self.result()

    def __setitem__(self, name, value):
        """Set an option's value using dict style access.

        :<py>:

            vim.options['{name}'] = {value!r}
        """
        self._vs.execute(self.mycode().format(name=name, value=value))

    def __setattr__(self, name, value):
        """Set an option's value using attr style access.

        :<py>:

            vim.options.{name} = {value!r}
        """
        self._vs.execute(self.mycode().format(name=name, value=value))
