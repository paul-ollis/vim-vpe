"""Special handling of variables."""
# pylint: disable=deprecated-method

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support

import vpe

_run_after = ['test_vim.py']


class Variables(support.Base):
    """Basic behaviour of variables."""

    @test(testID='global-variables')
    def global_variables(self):
        """Global variables may be read and set.

        Undefined variables have a value of ``None``.

        :<py>:

            res = Struct()
            vars = vim.vars

            res.undef_var = vars.test_var
            vars.test_var = 123
            res.set_var = vars.test_var

            dump(res)
        """
        res = self.run_self()
        failUnless(res.undef_var is None)
        failUnlessEqual(123, res.set_var)

    @test(testID='vim-variables')
    def vim_variables(self):
        """Vim (v:name) variables may be read and set.

        The ability to set 'v:name' variables is an extension.

        Undefined variables have a value of ``None``.

        :<py>:

            res = Struct()
            vvars = vim.vvars

            vvars.errmsg = 'Oops'
            res.set_var = vvars.errmsg
            vvars.errmsg = 'Oops again'
            res.set_var_again = vvars.errmsg

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual('Oops', res.set_var)
        failUnlessEqual('Oops again', res.set_var_again)

    @test(testID='vim-var-undef')
    def vim_undef_variables(self):
        """Undefined (v:name) variables are handled sensibly.

        Undefined variables have a value of ``None``. Attempting to set an
        undefined variables raise AttributeError.

        :<py>:

            res = Struct()
            vvars = vim.vvars

            res.undef_var = vvars.test_var
            dump(res)
        """
        res = self.run_self()
        failUnless(res.undef_var is None)
        failUnlessRaises(
            AttributeError, setattr, vpe.vim.vvars, 'test_var', 123)


if __name__ == '__main__':
    runModule()
