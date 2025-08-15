"""Special Vim application user interface support.

This provides special support for the overall Vim application user interface.
It only works on X.Org based desktops and then only if the correct programs
are available.
"""

import platform

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import Collection
from cleversheep3.Test.Tester import test, runModule

import support

import vpe

_run_after = ['test_vim.py']

if platform.platform().startswith('CYGWIN'):
    raise Collection.Unsupported


class PanelViewBuffer(support.Base):
    """VPE support organised display within a ScratchBuffer."""

    @test(testID='app-ui-query')
    def app_ui_query(self):
        """Details about the application's UI can be queried.

        :<py>:

            from vpe import app_ui_support

            res = Struct()

            displays = app_ui_support.get_display_info()
            win = app_ui_support.get_app_win_info()
            win = app_ui_support.get_app_win_info()  # For coverage!
            res.displays = displays.displays

            display = displays.find_display_for_window(win)
            res.display_x = display.x

            res.decor_dims = win.decor_dims
            res.columns = win.columns

            dump(res)
        """
        res = self.run_self()
        failUnless(isinstance(res.displays, list))
        failUnless(isinstance(res.display_x, int))
        failUnless(isinstance(res.decor_dims, tuple))
        if res.columns is not None:
            failUnless(98 <= res.columns <= 104)


if __name__ == '__main__':
    runModule()
