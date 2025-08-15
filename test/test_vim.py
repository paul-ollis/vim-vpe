"""The core VPE tests."""
# pylint: disable=too-many-lines,wrong-import-position
# pylint: disable=inconsistent-return-statements
# pylint: disable=deprecated-method

import re
import time

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support                             # pylint: disable=wrong-import-order

import vpe


class VimSuite(support.Base):
    """Basic behaviour of the Vim object."""

    def do_continue(self):
        """Continue Vim session to allow ``res`` to be dumped.

        :<py>:

            dump(res)
        """
        return self.run_self()

    def get_log(self):
        """Continue Vim session, saveing the log's lines.

        :<py>:

            res.log = vpe.log.lines
            dump(res)
        """
        return self.run_self()

    @classmethod
    def extract_from_lines(
            cls, lines: list[str], pattern: str, after: str = '') -> str:
        """Extract a line from a list of lines, using a search pattern."""
        if after:
            for line in lines:
                if line == after:
                    break
            else:
                return ''

        for line in lines:
            if re.search(pattern, line):
                return line
        return ''

    @classmethod
    def extract_log_line(
            cls, lines: list[str], pattern: str) -> str:
        """Extract a line from a list of log lines, using a search pattern."""

        line = cls.extract_from_lines(lines, pattern)
        m = re.match('^ *[0-9]+[.][0-9]{2}: (.*)', line)
        if m:
            line = m.group(1)
        else:
            line = line[9:]
        return line.rstrip()

    @test(testID='vim-singleton')
    def singleton(self):  # pylint: disable=no-self-use
        """The Vim class instantiates as a singleton."""
        failUnless(vpe.Vim() is vpe.vim)

    @test(testID='standard-members')
    def all_members_provided(self):
        """The Vim class replicates the vim module members.

        :<py>:

            members = {}
            member_names = (
                'command', 'eval', 'bindeval', 'strwidth', 'foreach_rtp',
                'chdir', 'fchdir', 'error', 'buffers', 'windows', 'tabpages',
                'current', 'vars', 'vvars', 'options')
            for name in member_names:
                members[name] = (vim, name, None)
            dump(members)
        """
        members = self.run_self()
        for aname, attr in members.items():
            failIf(attr is None, f'Vim has no {aname} member')

    @test(testID='read-only-attrs')
    def attrs_are_read_only(self):
        """The Vim object's attributes are mostly read-only.

        This prevents, for example, accidentally making the buffers
        inaccessible.
        """
        for aname in (
                'buffers', 'vars', 'vvars', 'windows', 'options', 'tabpages',
                'current'):
            failUnlessRaises(AttributeError, setattr, self.vim, aname, '')

    @test(testID='return-type-wrapping')
    def return_types_are_wrapped(self):
        """The Vim types are wrapped for function calls.

        The Vim object exposes most Vim functions as methods. The VPE wrapping
        performs automatic conversion of some vim module types to more natural
        Python types.
        """
        failUnless(isinstance(
            self.eval('vim.getcharsearch()'),
            vpe.common.MutableMappingProxy))
        print(type(self.eval('vim.timer_info(0)')))
        failUnless(isinstance(
            self.eval('vim.timer_info(0)'), vpe.common.MutableSequenceProxy))
        failUnless(isinstance(self.eval('vim.string(0)'), str))
        failUnless(isinstance(self.eval('vim.abs(-1)'), int))
        failUnless(isinstance(self.eval('vim.ceil(1.5)'), float))

    @test(testID='temp-options-1')
    def temp_options_context(self):
        """Vim.temp_options makes it easy to work with different option values.

        Changes made when the context manager is active get restored.

        :<py>:

            res = Struct()
            bg = _vim.options['background']
            alt_bg = b'dark' if bg == b'light' else b'light'
            res.orig_bg = bg
            res.alt_bg = alt_bg
            with vim.temp_options() as temp_opt:
                temp_opt['background'] = alt_bg
                res.in_context_bg = _vim.options['background']
            res.post_context_bg = _vim.options['background']

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.alt_bg, res.in_context_bg)
        failUnlessEqual(res.orig_bg, res.post_context_bg)

    @test(testID='temp-options-2')
    def temp_options_context_init_vals(self):
        """Vim.temp_options can have preset values for the context.

        Changes made via context manager is active get restored.

        :<py>:

            res = Struct()
            bg = _vim.options['background']
            alt_bg = b'dark' if bg == b'light' else b'light'
            res.orig_bg = bg
            res.alt_bg = alt_bg
            temp_opt_cm = vim.temp_options(background=alt_bg)
            res.pre_context_bg = _vim.options['background']
            with temp_opt_cm:
                res.in_context_bg = _vim.options['background']
            res.post_context_bg = _vim.options['background']

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.orig_bg, res.pre_context_bg)
        failUnlessEqual(res.alt_bg, res.in_context_bg)
        failUnlessEqual(res.orig_bg, res.post_context_bg)

    @test(testID='default-option')
    def reset_options(self):
        """The VI_DEFAULT and VIM_DEFAULT constants allow option resetting.

        :<py>:

            res = Struct()
            o = vim.options
            o.esckeys = True
            res.orig_esc_keys = o.esckeys
            o.esckeys = vpe.VI_DEFAULT
            res.vi_esc_keys = o.esckeys
            o.esckeys = vpe.VIM_DEFAULT
            res.vim_esc_keys = o.esckeys

            dump(res)
        """
        res = self.run_self()
        failUnless(res.orig_esc_keys)
        failIf(res.vi_esc_keys)
        failUnless(res.vim_esc_keys)

    @test(testID='vim-to-py-script')
    def vim_to_py_script(self):
        """The script_py_path function converts source path to python path.

        :<py>:

            res = Struct()
            res.py_path = vpe.script_py_path()
            dump(res)
        """
        with open('/tmp/script.vim', 'wt') as f:
            f.write('py3file /tmp/test.py\n')
        with open('/tmp/test.py', 'wt') as f:
            code_text, _ = self.mycode()
            f.write(code_text)
        self.vs.execute_vim_command('source /tmp/script.vim')
        res = self.result()
        failUnless('/tmp/script.py', res.py_path)

    @test(testID='vim-registers')
    def vim_registers(self):
        """The registers property allows read/write access to the registers.

        :<py>:

            res = Struct()
            vim.registers['a'] = 'Hello'
            res.a1 = vim.registers['a']
            res.a2 = vim.eval('@a')
            vim.registers['a'] = 'Bye'
            res.a3 = vim.eval('@a')
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('Hello', res.a1)
        failUnlessEqual('Hello', res.a2)
        failUnlessEqual('Bye', res.a3)

    @test(testID='vim-functions')
    def vim_functions(self):
        """Vim functions appear as methods of the Vim class.

        :<py>:

            res = Struct()
            a = [1, 2, 3]
            b = [4, 5, 6]
            combined = vim.extend(a, b)
            print("X", combined)
            res.combined = list(combined)

            getcharsearch = vim.getcharsearch
            res.type_str = str(type(getcharsearch))
            res.name  = getcharsearch.name

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual([1, 2, 3, 4, 5, 6], res.combined)
        failUnlessEqual("<class 'vpe.common.Function'>", res.type_str)
        failUnlessEqual('getcharsearch', res.name)

    @test(testID='vim-function-error')
    def vim_function_error(self):
        """Vim function call errors generate VimError.

        The VimError is a subclass of vim.error, that can provide more data.
        The VPE code will print details of the error, which for tests, goes to
        the log.

        :<py>:

            def doit():
                args = tuple(f'arg-{i}' for i in range (10))
                kwargs = {f'arg-{i}': i for i in range (10)}
                try:
                    vim.expand([], '', *args, **kwargs)
                except vpe.VimError as e:
                    res.error_str = str(e)
                    res.code = getattr(e, 'code', None)
                    res.command = getattr(e, 'command', None)
                    res.message = getattr(e, 'message', None)
                res.done = True
                res.log= vpe.log.lines
                dump(res)

            # We have to run our code using ``call_soon`` because this code is
            # invoked remotely and Vim suppresses exceptions during the remote
            # evaluation.
            vpe.log.clear()
            res = Struct()
            vpe.call_soon(doit)
        """
        def done():
            if res is None or res.log is None:
                return False
            if len(res.log) < 3:
                return False
            return True

        res = self.run_self()
        a = time.time()
        res = self.do_continue()
        while time.time() - a < 1.0 and not done():
            time.sleep(0.05)
            res = self.get_log()

        failUnlessEqual(
            'Vim:E118: Too many arguments for function: expand',
            res.error_str)
        failUnlessEqual(118, res.code)
        failUnlessEqual('', res.command)
        failUnlessEqual('Too many arguments for function: expand', res.message)

        failUnlessEqual(
            'VPE: Function[expand].__call__ failed:'
            ' Vim:E118: Too many arguments for function: expand',
            self.extract_log_line(res.log, '__call__.failed'))
        failUnlessEqual(
            '    self.args=None',
            self.extract_log_line(res.log, 'self.args='))
        failUnlessEqual(
            '    self.self=None',
            self.extract_log_line(res.log, 'self='))
        failUnlessEqual(
            "    args=([],",
            self.extract_log_line(res.log, r'args=\('))
        failUnlessEqual(
            "    kwargs={'arg-0': 0,",
            self.extract_log_line(res.log, r'kwargs=\{'))
        failUnlessEqual(
            '    vim.state()=c',
            self.extract_log_line(res.log, r'vim.state\('))

    @test(testID='vim-function-error-2')
    def vim_function_error2(self):
        """The VimError can be caught as vim.error.

        :<py>:

            def doit():
                try:
                    vim.expand([], '')
                except vim.error as e:
                    res.error_str = str(e)
                    res.code = getattr(e, 'code', None)
                    res.command = getattr(e, 'command', None)
                    res.message = getattr(e, 'message', None)
                res.done = True
                dump(res)

            # We have to run our code using ``call_soon`` because this code is
            # invoked remotely and Vim suppresses exceptions during the remote
            # evaluation.
            res = Struct()
            vpe.call_soon(doit)
        """
        res = self.run_self()
        a = time.time()
        res = self.do_continue()
        while time.time() - a < 1 and (res is None or res.done is None):
            time.sleep(0.05)

        failUnlessEqual('Vim:E730: Using a List as a String', res.error_str)
        failUnlessEqual(730, res.code)
        failUnlessEqual('', res.command)
        failUnlessEqual('Using a List as a String', res.message)

    @test(testID='vim-function-error-3')
    def vim_function_error_suppression(self):
        """Failed function call logging and exception can be suppressed.

        :<py>:

            def doit():
                try:
                    with vpe.suppress_vim_invocation_errors:
                        vim.expand([], '')
                except vpe.VimError as e:
                    res.error_str = str(e)
                    res.code = getattr(e, 'code', None)
                    res.command = getattr(e, 'command', None)
                    res.message = getattr(e, 'message', None)
                res.done = True
                res.log= vpe.log.lines
                dump(res)

            # We have to run our code using ``call_soon`` because this code is
            # invoked remotely and Vim suppresses exceptions during the remote
            # evaluation.
            vpe.log.clear()
            res = Struct()
            vpe.call_soon(doit)
        """
        def done():
            if res is None or res.log is None:
                return False
            if len(res.log) < 3:
                return False
            return True

        res = self.run_self()
        a = time.time()
        res = self.do_continue()
        while time.time() - a < 1.0 and not done():
            time.sleep(0.05)
            res = self.get_log()

        failUnless(res.error_str is None)
        failUnlessEqual('', self.extract_log_line(res.log, '__call__.failed'))

    @test(testID='vim-function-nonexistant')
    def vim_function_does_not_exist(self):
        """A non-existant Vim function raises an AttributeError.

        :<py>:

            try:
                vim.no_such_function
            except AttributeError:
                res.attr_error = True
            else:
                res.attr_error = False

            dump(res)
        """
        res = self.run_self()
        failUnless(res.attr_error)
