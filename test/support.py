"""Common test support."""

import functools
import os
import pathlib
import subprocess
import time

from CleverSheep.Test import Tester
from CleverSheep.Test.Tester import *

VIM_NAME = 'TEST'

cons = functools.partial(print, file=console)


class VimClient:
    def __init__(self):
        os.environ['VIM3'] = 'y'

    def command(self, cmd):
        """Execute a colon prompt command.

        The command should be a single line. A trainling <CR> is appended.
        """
        subprocess.call([
            'vim', '--servername', 'TEST', '--remote-send',
            f'<C-\\><C-N>:{cmd}<CR>',
        ])

    def sync(self):
        """Forces wait for vim session to catch up.

        Whic uses --remote-expr, which waits for a response.
        """
        subprocess.run([
            'vim', '--servername', 'TEST', '--remote-expr', 'eval("0")'],
            capture_output=True)


class Result:
    def __init__(self, expr):
        _, _, details = expr.partition(': ')
        self.assert_expr, _, info = details.partition(' :: ')
        self.info = {}
        self.info = dict(e.split('=') for e in info.split(' :: ') if '=' in e)
        self.expr, _, self.value = self.assert_expr.partition('=')

    def __getattr__(self, name):
        return self.info.get(name, None)


class Fail(Result):
    def __bool__(self):
        return False


class Pass(Result):
    def __bool__(self):
        return True


def get_test_results(path, test_id):
    active = False
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith('- Test-ID: '):
                active = line == f'- Test-ID: {test_id} -'
                continue
            if active:
                if line.startswith('PASS: '):
                    yield Pass(line)
                elif line.startswith('FAIL: '):
                    yield Fail(line)


def check_result(result):

    def format_assert_equal_failure():
        s = [f'Details:']
        for k in sorted(result.info):
            s.append(f'\n    {k}={result.info[k]}')
        return ''.join(s)

    failUnless(result, makeMessage=format_assert_equal_failure)
