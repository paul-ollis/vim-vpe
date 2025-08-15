"""Special handling of tabpages."""
# pylint: disable=deprecated-method

from functools import partial

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support

import vpe

_run_after = ['test_vim.py']


class TabPages(support.Base):
    """VPE support for standard tabpages.

    VPE provides the `TabPage` class that wraps a :vim:`python-tabpage`. The
    TabPage may be used in the same manner as :vim:`python-tabpage`, but has
    some enhancements.
    """
    tabpage: vpe.wrappers.TabPage

    def suiteSetUp(self):
        """called to set up the suite.
        :<py>:

            vpe.commands.tabonly()
        """
        super().suiteSetUp()
        self.run_self()
        self.tabpage = self.eval('vim.current.tabpage')

    @test(testID='tab-ro-attrs')
    def read_only_attrs(self):
        """Certain TabPage attributes are read-only."""
        tabpage = self.tabpage
        attrErrorCheck = partial(failUnlessRaises, AttributeError)
        attrErrorCheck(setattr, tabpage, 'windows', tabpage.windows)
        attrErrorCheck(setattr, tabpage, 'vars', tabpage.vars)
        attrErrorCheck(setattr, tabpage, 'number', tabpage.number)
        attrErrorCheck(setattr, tabpage, 'window', tabpage.window)
        attrErrorCheck(setattr, tabpage, 'valid', tabpage.valid)

    @test(testID='tab-vars-attr')
    def tabpage_vars_as_attributes(self):
        """TabPage.vars provides attribute style access.

        This is in addition to dictionary style access; making for more
        naturalistic code.

        :<py>:

            res = Struct()
            tabpage = vim.current.tabpage
            tabpage.vars.temp_var = 'Hello'
            res.temp_var = _vim.bindeval('t:temp_var')
            res.alt_temp_var = tabpage.vars.temp_var

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(b'Hello', res.temp_var)
        failUnlessEqual('Hello', res.alt_temp_var)

    @test(testID='tab-valid-flag')
    def tabpage_valid_flag(self):
        """TabPage.valid attribute is set to False when a tabpage is closed.

        :<py>:

            res = Struct()
            vpe.commands.tabnew()
            tabpage = vim.tabpages[1]
            res.orig_valid = tabpage.valid
            vpe.commands.wincmd('c')
            res.new_valid = tabpage.valid

            dump(res)
        """
        res = self.run_self()
        failUnless(res.orig_valid)
        failIf(res.new_valid)

    @test(testID='new-tab-page')
    def new_tab_page(self):
        """TabPage.new creates a new page in a controlled manner.

        The new tab page can be created to be before or after the current tab
        page; or as the first or last page.

        :<py>:

            res = Struct()

            pages = vim.tabpages

            fourth = vim.current.tabpage
            fourth.vars.name = 'four'

            fifth = pages.new()
            fifth.vars.name = 'five'
            res.first_pair = fourth.number, fifth.number

            first = pages.new(position='first')
            first.vars.name = 'one'

            last = pages.new(position='last')
            last.vars.name = 'six'

            third = pages.new()
            third.vars.name = 'three'

            second = pages.new(position='before')
            second.vars.name = 'two'

            res.names = [t.vars.name for t in (
                first, second, third, fourth, fifth, last)]
            dump(res)
        """
        # TODO: Vim -bug: I have seem Vim segfault when this test is run.
        res = self.run_self()
        failUnlessEqual((1, 2), res.first_pair)
        failUnlessEqual(
            ['one', 'two', 'three', 'four', 'five', 'six'], res.names)


if __name__ == '__main__':
    runModule()
