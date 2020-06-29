import contextlib
import inspect
import pathlib
import traceback

import vpe

vim = vpe.Vim()
_vim = vim.vim()
bufs = vim.buffers
wins = vim.windows
tabs = vim.tabpages
vars = vim.vars
vvars = vim.vvars
options = vim.options


class Assertion:
    def __init__(self, expr, **kwargs):
        self.expr = expr
        self.keyvals = kwargs
        self.keyvals['expr'] = repr(expr)
        self.ok = False
        self.raised = None
        if isinstance(expr, str):
            try:
                self.keyvals['result'] = self.result = eval(expr)
                self.ok = True
            except Exception as e:
                self.keyvals['result'] = f'Could not evalate {self.expr!r}'
                self.keyvals['error'] = f'{e}'
                self.raised = e
        else:
            self.keyvals['result'] = (
                f'Could not evalate non-string ({self.expr!r})')

    def invoke(self):
        stack = inspect.stack()
        self.keyvals['line'] = stack[2].frame.f_lineno
        del stack
        keyval_exprs = [
            f'{k}={v}' for k, v in self.keyvals.items() if v is not Ellipsis]
        self.info = ' :: ' + ' :: '.join(keyval_exprs) if keyval_exprs else ''
        if self.ok:
            print(f'PASS: {self.info}')
        else:
            print(f'FAIL: {self.info}')


class AssertEqual(Assertion):
    def __init__(self, expected, expr, **kwargs):
        super().__init__(expr, **kwargs)
        self.keyvals['expected'] = repr(expected)
        self.ok = self.ok and self.result == expected


class AssertTrue(Assertion):
    def __init__(self, expr, **kwargs):
        super().__init__(expr, **kwargs)
        self.ok = self.ok and self.result
        self.keyvals['test'] = 'True assertion'


class AssertFalse(Assertion):
    def __init__(self, expr, **kwargs):
        super().__init__(expr, **kwargs)
        self.ok = self.ok and not self.result
        self.keyvals['test'] = 'False assertion'


class AssertRaises(Assertion):
    def __init__(self, exc, expr, **kwargs):
        super().__init__(expr, **kwargs)
        self.ok = isinstance(self.raised, exc)
        if not self.ok:
            self.keyvals['result'] = f'Did not raise {exc}'
            self.keyvals['raised'] = self.raised.__class__.__name__
            self.keyvals.pop('error', None)


class AssertNoException(Assertion):
    def __init__(self, expr, **kwargs):
        super().__init__(expr, **kwargs)
        self.ok = self.raised is None
        if not self.ok:
            self.keyvals['result'] = f'Raised {self.raised.__class__.__name__}'
            self.keyvals['message'] = str(self.raised)
            self.keyvals['raised'] = self.raised.__class__.__name__
            self.keyvals.pop('error', None)


def assert_equal(*args, **kwargs):
    AssertEqual(*args, **kwargs).invoke()


def assert_true(*args, **kwargs):
    AssertTrue(*args, **kwargs).invoke()


def assert_false(*args, **kwargs):
    AssertFalse(*args, **kwargs).invoke()


def assert_raises(*args, **kwargs):
    AssertRaises(*args, **kwargs).invoke()


def assert_no_exception(*args, **kwargs):
    AssertNoException(*args, **kwargs).invoke()


def to_str(s):
    try:
        return s.decode()
    except AttributeError:
        return s


def get_test_buffer(rerun=False, goto=False):
    for buf in vim.buffers:
        if buf.name.endswith('/--TEST--'):
            break
    else:
        if rerun:
            return None
        vim.command('silent! edit --TEST--')
        return get_test_buffer(rerun=True)

    _buf = buf._proxied
    _buf.options['modifiable'] = True
    with dropped_messages():
        _buf[:] = []
    if goto:
        _vim.command(f'silent! buffer {_buf.number}')
    return buf, _buf


@contextlib.contextmanager
def dropped_messages():
    _vim.command(f'redir >>/dev/null')
    try:
        yield
    finally:
        _vim.command(f'redir! >{msg_path}')


@contextlib.contextmanager
def test_context(data_path):
    global msg_path

    msg_path = f'{data_path}.msg'
    with open(data_path, 'wt') as f:
        with contextlib.redirect_stdout(f):
            _vim.command(f'redir! >{msg_path}')
            try:
                yield None
            finally:
                _vim.command(f'redir END')
                sentinel = pathlib.Path(data_path).parent / 'sentinel'
                sentinel.touch(exist_ok=True)


@contextlib.contextmanager
def double_split_window_context():
    _vim.command('split')
    _vim.command('vert split')
    yield None
    _vim.command('only')
