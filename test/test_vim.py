"""The core VPE tests."""
# pylint: disable=too-many-lines,wrong-import-position
# pylint: disable=inconsistent-return-statements
# pylint: disable=deprecated-method

from functools import partial

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support

import vpe


class VimSuite(support.Base):
    """Basic behaviour of the Vim object."""

    @test(testID='vim-singleton')
    def singleton(self):  # pylint: disable=no-self-use
        """The Vim class instantiates as a singleton."""
        failUnless(vpe.Vim() is vpe.vim)

    @test(testID='standard-members')
    def all_members_provided(self):
        """The Vim replicates the vim module members.

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
    def attr_types(self):
        """The Vim object's attributes are read-only.

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

        The Vim object exposes most Vim functiona as methods. The vim.Function
        class used for this, which results in types like vim.Dictionary being
        returned. VPE automaticaly wraps these in easier to use types.
        """
        failUnless(isinstance(
            self.eval('vim.getcharsearch()'),
            vpe.wrappers.MutableMappingProxy))
        print(type(self.eval('vim.timer_info(0)')))
        failUnless(isinstance(
            self.eval('vim.timer_info(0)'), vpe.wrappers.MutableSequenceProxy))
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
            f.write(self.mycode())
        self.vs.execute_vim('source /tmp/script.vim')
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


if __name__ == '__main__':
    runModule()
