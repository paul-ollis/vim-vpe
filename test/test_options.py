"""Special handling of options."""
# pylint: disable=deprecated-method

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support

import vpe

_run_after = ['test_vim.py']


class Options(support.Base):
    """Basic behaviour of the options."""

    @test(testID='comma-sep-flag-options')
    def commas_separated_flag_option(self):
        """Comma separated options are elegantly handled.

        The '+=' and '-=' operators add/remove characters from the flag set.
        It is not an error to add or remove a character twice. Multiple flags,
        separated by commas, may appear on the RHS of an assignment.
        """
        vim_options = self.vim_options
        failUnlessEqual('', vim_options.whichwrap)
        vim_options['whichwrap'] = 'b,s,h'
        failUnlessEqual('b,s,h', vim_options.whichwrap)
        vim_options.whichwrap -= 's'
        failUnlessEqual('b,h', vim_options.whichwrap)
        vim_options.whichwrap += 's'
        failUnlessEqual('b,h,s', vim_options.whichwrap)

        vim_options.whichwrap += 's'
        failUnlessEqual('b,h,s', vim_options.whichwrap)

        vim_options.whichwrap -= 'h'
        failUnlessEqual('b,s', vim_options.whichwrap)
        vim_options.whichwrap -= 'h'
        failUnlessEqual('b,s', vim_options.whichwrap)

        vim_options['whichwrap'] = 'b,s,h'
        failUnlessEqual('b,s,h', vim_options.whichwrap)
        vim_options.whichwrap -= 'h,b'
        failUnlessEqual('s', vim_options.whichwrap)

        vim_options.whichwrap += 'h,s,b'
        failUnlessEqual('s,h,b', vim_options.whichwrap)

    @test(testID='flag-options')
    def flag_option(self):
        """Flag options are elegantly handled.

        The same basic rules as for comma separated options apply.
        """
        vim_options = self.vim_options
        vim_options.mouse = 'na'
        failUnlessEqual('na', vim_options.mouse)
        vim_options.mouse += 'nvic'
        failUnlessEqual('navic', vim_options.mouse)
        vim_options.mouse -= 'ni'
        failUnlessEqual('avc', vim_options.mouse)

    @test(testID='global-options')
    def global_option(self):
        """The Vim.options specifically modify the global options."""
        vim_options = self.vim_options
        _vim = vpe._vim  # pylint: disable=protected-access
        vim_options.cinwords = 'for,if'
        failUnlessEqual('for,if', vim_options.cinwords)
        failUnlessEqual('for,if', _vim.options.cinwords)

        vim_options.cinwords = 'for,if,else'
        failUnlessEqual('for,if,else', vim_options.cinwords)
        failUnlessEqual('for,if,else', _vim.options.cinwords)

    @test(testID='set-unknown-option')
    def set_unknown_option(self):
        """Setting an unknown option is an Attribute error."""
        vim_options = self.vim_options
        failUnlessRaises(AttributeError, setattr, vim_options, 'aardvark', 99)

    @test(testID='get-unknown-option')
    def get_unknown_option(self):
        """Getting an unknown option is an Attribute error."""
        vim_options = self.vim_options
        failUnlessRaises(AttributeError, getattr, vim_options, '__name__')
        failUnlessRaises(AttributeError, getattr, vim_options, 'aardvark')

    @test(testID='option-set_global-local')
    def option_set_global_local(self):
        """It is possible to set global-local options.

        The vim module interface does not (fully?) support this.
        """
        vim_options = self.vim_options
        vim_options.autoindent = False
        failIf(vim_options.autoindent)
        vim_options.autoindent = True
        failUnless(vim_options.autoindent)

        vim_options.fileformat = 'dos'
        failUnlessEqual('dos', vim_options.fileformat)
        vim_options.fileformat = 'unix'
        failUnlessEqual('unix', vim_options.fileformat)


class CommaListOptions(support.Base):
    """Special handling of comma separated list options"""

    @test(testID='comm-list-options')
    def list_option(self):
        """Comma list options are elegantly handled.

        The same basic rules as for character list options apply.
        """
        vim_options = self.vim_options
        vim_options.tags = ''
        failUnlessEqual('', vim_options.tags)
        vim_options.tags += 'tags,random.tags'
        failUnlessEqual('tags,random.tags', vim_options.tags)
        vim_options.tags += 'mytags,hertags'
        failUnlessEqual('tags,random.tags,mytags,hertags', vim_options.tags)
        vim_options.tags -= 'tags,hertags'
        failUnlessEqual('random.tags,mytags', vim_options.tags)

    @test(testID='comma-list-bad-type')
    def list_option_bad_add(self):
        """Adding or removing a non-string raises a type error."""

        def try_add():
            vim_options.tags += 123

        def try_sub():
            vim_options.tags -= 123

        vim_options = self.vim_options
        vim_options.tags = ''
        failUnlessRaises(TypeError, try_add)
        failUnlessRaises(TypeError, try_sub)


if __name__ == '__main__':
    runModule()
