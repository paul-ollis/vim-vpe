"""Various extensions in VPE."""

import time

# pylint: disable=deprecated-method
# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import Collection
from cleversheep3.Test.Tester import test, runModule

import support                             # pylint: disable=wrong-import-order
import vim_if

_run_after = ['test_vim.py']

if vim_if.VimSession.get_version() < [8, 2]:
    raise Collection.Unsupported


class Popup(support.Base):
    """Poup window.

    The Popup class provides a Pythonic interface for managing popup windows.
    """
    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            class MyPopup(vpe.Popup):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.result = None
                    self.keys = []

                def on_close(self, result: int) -> None:
                    self.result = result

                def on_key(self, key: str, byte_seq: bytes) -> bool:
                    self.keys.append((key, byte_seq))
                    if key == 'k':
                        return super().on_key(key, byte_seq)
                    return True

            def save_info():
                res.options = vim.popup_getoptions(pid)
                res.pos = vim.popup_getpos(pid)
                bufnum = vim.winbufnr(pid)
                if bufnum > 0:
                    buf = vim.buffers[bufnum]
                    res.lines = list(buf)
                else:
                    res.lines = None
        """
        super().suiteSetUp()
        self.run_self()

    def suiteTearDown(self):
        """Called to cleanup after the suite ends.

        :<py>:

            vpe.popup_clear()
            vpe.commands.redraw()
        """
        self.run_self()
        super().suiteTearDown()

    @test(testID='popup-create')
    def create_popup(self):
        """Create a simple popup, using a scratch buffer.

        :<py>:
            popup = MyPopup(['One', 'Two', 'Three'], name='Testing')
            pid = popup.id
            res = Struct()
            save_info()
            res.buf_lines = list(popup.buffer)
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['One', 'Two', 'Three'], res.lines)
        failUnlessEqual(['One', 'Two', 'Three'], res.buf_lines)

    @test(testID='popup-hide-show')
    def create_show_hide(self):
        """The popup can be hidden or shown.

        :<py>:
            popup = MyPopup(['One', 'Two', 'Three'])
            pid = popup.id
            res = Struct()
            save_info()
            res.vis_a = res.pos['visible']
            res.vis_aa = popup.visible

            popup.hide()
            save_info()
            res.vis_b = res.pos['visible']
            res.vis_bb = popup.visible

            popup.show()
            save_info()
            res.vis_c = res.pos['visible']
            res.vis_cc = popup.visible

            dump(res)
        """
        res = self.run_self()
        failUnless(res.vis_a)
        failUnless(res.vis_aa)
        failIf(res.vis_b)
        failIf(res.vis_bb)
        failUnless(res.vis_c)
        failUnless(res.vis_cc)

    @test(testID='popup-can-survive')
    def popup_survives_for_display_buffer(self):
        """A popul backed by a display buffer survives destruction by Vim.

        :<py>:
            res = Struct()

            # Create a named popup, which get backed by a display buffer.
            # Close it immediately, which will cause Vim to discard the popup
            # instance.
            popup = MyPopup(['One', 'Two', 'Three'], name='Testing')
            popup.close(1)
            res.result_a = popup.result

            # Show the popup again and close again.
            popup.show()
            popup.close(2)
            res.result_b = popup.result

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.result_a)
        failUnlessEqual(2, res.result_b)

    @test(testID='popup-settext')
    def create_settext(self):
        """The text in a popup can be set post-creation.

        :<py>:
            res = Struct()
            popup = MyPopup(['One', 'Two', 'Three'])
            popup.settext(['Two', 'Three', 'Four'])
            pid = popup.id
            save_info()
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['Two', 'Three', 'Four'], res.lines)

    @test(testID='popup-set-multi-options')
    def popup_set_multi_options(self):
        """Multiple options can be set at once.

        :<py>:
            res = Struct()
            popup = MyPopup(['One', 'Two', 'Three'])

            res.before_col = popup.col
            res.before_line = popup.line

            popup.setoptions(col=res.before_col + 1, line=res.before_line + 2)
            res.after_col = popup.col
            res.after_line = popup.line
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.before_col + 1, res.after_col)
        failUnlessEqual(res.before_line + 2, res.after_line)

    @test(testID='popup-multi-move-options')
    def popup_multi_move_options(self):
        """Multiple move options can be set at once.

        :<py>:
            res = Struct()
            popup = MyPopup(['One', 'Two', 'Three'])

            res.before_col = popup.col
            res.before_line = popup.line

            popup.move(col=res.before_col + 1, line=res.before_line + 2)
            res.after_col = popup.col
            res.after_line = popup.line
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(res.before_col + 1, res.after_col)
        failUnlessEqual(res.before_line + 2, res.after_line)

    @test(testID='popup-clearall')
    def create_clearall(self):
        """The clear method.

        This invokes popup_clear, but also performs VPE house keeping.

        :<py>:
            res = Struct()

            popup2 = MyPopup(['Second'])
            popup = MyPopup(['One', 'Two', 'Three'])
            res.init_num_popups = len(popup._popups)

            popup.clear(force=False)
            res.num_popups = len(vim.popup_list())

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(2, res.init_num_popups)
        failUnlessEqual(0, res.num_popups)

    @test(testID='popup-close')
    def close_popup(self):
        """The on_close method is invoked.

        :<py>:
            res = Struct()

            popup = MyPopup(['One', 'Two', 'Three'])
            popup.close(99)
            res.result = popup.result
            res.buf = popup.buffer

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(99, res.result)
        failUnless(res.buf is None)

    @test(testID='popup-autoclose')
    def popup_autoclose(self):
        """A popup can automatically close using a timeout.

        :<py>:
            res = Struct()

            popup = MyPopup(['One', 'Two', 'Three'], time=30)
            res.result = popup.result
            res.buf = popup.buffer

            dump(res)
        """
        res = self.run_self()
        a = time.time()
        while time.time() - a < 0.5 and res.result is None:
            res = self.do_continue_get_popup_result()
        failUnlessEqual(-2, res.result)

    @test(testID='popup-notification')
    def popup_notification(self):
        """A notification popup has special handling in VPE.

        The behaviour is essentially the same, but the popup_notification()
        function has issues when invoked from Python land, hence VPE uses
        popup_create() with appropriate options.

        The notification popup has a timeout by default, but that is for 3
        seconds and we override it for testing.

        :<py>:
            class NotePopup(vpe.PopupNotification):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.result = None
                    self.keys = []

                def on_close(self, result: int) -> None:
                    self.result = result

                def on_key(self, key: str, byte_seq: bytes) -> bool:
                    self.keys.append((key, byte_seq))
                    if key == 'k':
                        return super().on_key(key, byte_seq)
                    return True

            res = Struct()

            popup = NotePopup(['One', 'Two', 'Three'], time=30)
            res.result = popup.result
            res.buf = popup.buffer

            dump(res)
        """
        res = self.run_self()
        a = time.time()
        while time.time() - a < 0.5 and res.result is None:
            res = self.do_continue_get_popup_result()
        failUnlessEqual(-2, res.result)

    @test(testID='popup-keys')
    def handle_keys(self):
        """The on_key method is invoked when keys are pressed.

        Special keys are converted into symbolic names such as '<F6>'.

        :<py>:
            res = Struct()

            popup = MyPopup(['One', 'Two', 'Three'])
            vpe.feedkeys(r'j\<F6>k', mode='n')

            dump(res)
        """
        self.run_self()
        res = self.do_continue()
        failUnlessEqual(('j', b'j'), res.keys[0])
        failUnlessEqual('<F6>', res.keys[1][0])
        failUnlessEqual(('k', b'k'), res.keys[2])

    def do_continue_get_popup_result(self):
       """Contine execution, collecting the popup result.

        :<py>:
            print(popup, popup.result)
            res.result = popup.result
            dump(res)
       """
       return self.run_self()

    def do_continue(self):
       """Continue execution to allow fed in keys to be processed.

        :<py>:
            # Grab last three keys.
            # I seem to have hit on a Vim bug. Creating a new buffer causes
            # extra keys to appear in the key buffer, but only when feedkeys
            # is invoked. For now I am skipping over the rogue keys.
            try:
                res.keys = popup.keys[-3:]
            except AttributeError:
                pass
            res.result = popup.result
            dump(res)
       """
       return self.run_self()

    @test(testID='popup-options')
    def popup_options(self):
        """Options are exposed as attributes.

        :<py>:
            res = Struct()

            popup = MyPopup(['One', 'Two', 'Three'])

            res.orig_line = vim.popup_getpos(popup.id)['line']
            popup.line = popup.line + 1
            res.new_line = vim.popup_getpos(popup.id)['line']

            res.orig_zindex = vim.popup_getoptions(popup.id)['zindex']
            popup.zindex = popup.zindex + 2
            res.new_zindex = vim.popup_getoptions(popup.id)['zindex']

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.new_line - res.orig_line)
        failUnlessEqual(2, res.new_zindex - res.orig_zindex)

    @test(testID='popup-dialog')
    def popup_dialog(self):
        """The PopupDialog class handles y/n keys.

        :<py>:
            res = Struct()

            popup = vpe.PopupDialog(['One', 'Two', 'Three'])
            vpe.feedkeys(r'y', literal=True, mode='n')

            dump(res)
        """
        self.run_self()
        res = self.do_continue()
        failUnlessEqual(1, res.result)

    @test(testID='popup-menu')
    def popup_menu(self):
        """The PopupMenu class handles up/down/enter keys.

        :<py>:
            res = Struct()

            popup = vpe.PopupMenu(['One', 'Two', 'Three'])
            vpe.feedkeys(r'\<Down>\<CR>', mode='n')

            dump(res)
        """
        self.run_self()
        res = self.do_continue()
        failUnlessEqual(2, res.result)


if __name__ == '__main__':
    runModule()
