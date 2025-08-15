"""Scratch buffers organised into panels.

The main class is the PanelViewBuffer, which is a ScratchBuffer specialised to
be organised as a sequence of horizontal panels. Each panel maps onto a
sequence of lines (possible zero length) within the buffer.

The user must subclass Panel in order to generate the content for the
PanelViewBuffer.
"""
# pylint: disable=deprecated-method

from functools import partial

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support
import vim_if
from support import fix_path

import vpe

_run_after = ['test_vim.py']


class PanelViewBuffer(support.Base):
    """VPE support organised display within a ScratchBuffer."""

    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            from vpe import panels

            class TestPanel(panels.Panel):
                def __init__(self, lines):
                    super().__init__()
                    self.test_lines = lines
                    self.lie_about_changes = False

                def on_format_contents(self):
                    self.content[:] = self.test_lines
                    if self.lie_about_changes:
                        self.view.notify_content_change(self)

            class TestView(panels.PanelViewBuffer):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.data.change_count = 0
                    self.data.reindex_count = 0

                def on_reindex(self):
                    self.data.reindex_count += 1

                def on_updates_applied(self, changes_occurred: bool):
                    self.data.change_count += 1 if changes_occurred else 0
        """
        super().suiteSetUp()
        self.run_suite_setup()
        # self.vim_buffers = self.eval('vim.buffers')

    @test(testID='pview-create')
    def create_a_panelview(self):
        """A panel view may be created, using get_display_buffer.

        It will have zero panels initially, which are accessible using the
        panels property.

        :<py>:

            from vpe import panels

            zap_bufs()
            res = Struct()

            buf = vpe.get_display_buffer('test-panels', buf_class=TestView)

            res.len_panels = len(buf.panels)
            res.change_count = buf.data.change_count
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(0, res.len_panels)
        failUnlessEqual(0, res.change_count)

    def setup_test_panels(self):
        """Set up a set of test panels.

        :<py>:

            from vpe import panels

            zap_bufs()
            res = Struct()

            buf = vpe.get_display_buffer('test-panels', buf_class=TestView)
            top = TestPanel(['Top'])
            middle = TestPanel(['Middle'])
            bottom = TestPanel(['Bottom'])
            buf.add_panel(top)
            buf.add_panel(middle)
            buf.add_panel(bottom)
        """
        self.run_self()

    @test(testID='pview-add-panels')
    def add_panels(self):
        """Panels may be added to the end of the panel list.

        When a panel is added the on_format_contents method is automatically
        invoked to set the (initial) contents.

        Each panel will have its own unique syntax prefix.

        :<py>:

            res.len_panels = len(buf.panels)
            res.content = list(buf)
            res.change_count = buf.data.change_count
            res.reindex_count = buf.data.reindex_count
            res.prefixes = [
                top.syntax_prefix,
                middle.syntax_prefix,
                bottom.syntax_prefix]
            dump(res)
        """
        self.setup_test_panels()
        res = self.run_self()
        failUnlessEqual(3, res.len_panels)
        failUnlessEqual(['Top', 'Middle', 'Bottom'], res.content)
        failUnlessEqual(3, res.change_count)
        failUnlessEqual(3, res.reindex_count)
        failUnlessEqual('Syn_testxpanels_0_', res.prefixes[0])
        failUnlessEqual('Syn_testxpanels_1_', res.prefixes[1])
        failUnlessEqual('Syn_testxpanels_2_', res.prefixes[2])

    @test(testID='pview-insert-panel-at-start')
    def insert_panel_at_start(self):
        """Panels may be inserted at the start of the panel list.

        As for adding, the on_format_contents method is automatically invoked
        to set the (initial) contents.

        :<py>:

            zero_panel = TestPanel(['Intro', 'panel'])
            buf.insert_panel(zero_panel, index=0)
            res.len_panels = len(buf.panels)
            res.content = list(buf)
            res.change_count = buf.data.change_count
            res.reindex_count = buf.data.reindex_count
            buf.show()
            dump(res)
        """
        self.setup_test_panels()
        res = self.run_self()
        failUnlessEqual(4, res.len_panels)
        failUnlessEqual(
            ['Intro', 'panel', 'Top', 'Middle', 'Bottom'], res.content)
        failUnlessEqual(4, res.change_count)
        failUnlessEqual(4, res.reindex_count)

    @test(testID='pview-insert-panel-in-middle')
    def insert_panel_in_middle(self):
        """Panels may be inserted within the panel list.

        As for adding, the on_format_contents method is automatically invoked
        to set the (initial) contents.

        :<py>:

            zero_panel = TestPanel(['Lower', 'middle'])
            buf.insert_panel(zero_panel, index=2)
            res.len_panels = len(buf.panels)
            res.content = list(buf)
            res.change_count = buf.data.change_count
            res.reindex_count = buf.data.reindex_count
            dump(res)
        """
        self.setup_test_panels()
        res = self.run_self()
        failUnlessEqual(4, res.len_panels)
        failUnlessEqual(
            ['Top', 'Middle', 'Lower', 'middle', 'Bottom'], res.content)
        failUnlessEqual(4, res.change_count)
        failUnlessEqual(4, res.reindex_count)

    @test(testID='pview-remove-insert')
    def remove_and_insert(self):
        """Panels may removed and then re-inserted.

        :<py>:

            new_panel = TestPanel(['Roamer'])
            buf.insert_panel(new_panel, index=1)
            res.content1 = list(buf)
            buf.remove_panel(new_panel)
            res.content2 = list(buf)
            buf.insert_panel(new_panel, index=2)
            res.content3 = list(buf)
            res.len_panels = len(buf.panels)
            res.change_count = buf.data.change_count
            res.reindex_count = buf.data.reindex_count
            dump(res)
        """
        self.setup_test_panels()
        res = self.run_self()
        failUnlessEqual(['Top', 'Roamer', 'Middle', 'Bottom'], res.content1)
        failUnlessEqual(['Top', 'Middle', 'Bottom'], res.content2)
        failUnlessEqual(['Top', 'Middle', 'Roamer', 'Bottom'], res.content3)
        failUnlessEqual(4, res.len_panels)
        failUnlessEqual(5, res.change_count)
        failUnlessEqual(6, res.reindex_count)

    @test(testID='pview-format-panel')
    def update_content(self):
        """The format_panel method is used to flush changes.

        When a panel's contents change, the format_panel method is used to
        request that the PanelViewBuffer makes all required adjustments.

        :<py>:

            vpe.commands.buffer(1)
            middle.test_lines = ['Central', 'panel']
            buf.format_panel(middle)
            res.content = list(buf)
            res.change_count = buf.data.change_count
            res.reindex_count = buf.data.reindex_count
            dump(res)
        """
        self.setup_test_panels()
        res = self.run_self()
        failUnlessEqual(['Top', 'Central', 'panel', 'Bottom'], res.content)
        failUnlessEqual(4, res.change_count)
        failUnlessEqual(4, res.reindex_count)

    @test(testID='pview-null-update')
    def null_update(self):
        """If a panel 'refresh' causes no actual change, nothing happens.

        :<py>:

            res.init_change_count = buf.data.change_count
            vpe.commands.buffer(1)
            middle.lie_about_changes = True
            buf.format_panel(middle)
            res.content = list(buf)
            res.reindex_count = buf.data.reindex_count
            buf.show()
            dump(res)
        """
        self.setup_test_panels()
        res = self.run_self()
        failUnlessEqual(['Top', 'Middle', 'Bottom'], res.content)
        failUnlessEqual(3, res.init_change_count)


class ConfigPanel(support.Base):
    """VPE support for panel holding configuration values."""

    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            from vpe import config
            from vpe import panels
            from vpe import ui

            class TestConfigView(
                    ui.ConfigPanelBuffer, panels.PanelViewBuffer):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.data.change_count = 0
                    self.data.sel_change_count = 0
                    self.auto_define_event_handlers('TestUIConfig')

                def on_first_showing(self):
                    super().on_first_showing()
                    self.auto_map_keys()

                def on_change(self):
                    self.data.change_count += 1

                def on_selected_field_change(self):
                    self.data.sel_change_count += 1

        """
        super().suiteSetUp()
        self.run_suite_setup()
        # self.vim_buffers = self.eval('vim.buffers')

    def setup_test_config_view(self):
        """Set up a ScratchBuffer supporting a config panel.

        :<py>:

            from vpe import panels
            from vpe import ui

            zap_bufs()
            res = Struct()

            conf_fields = {}
            bopt = config.Bool('bool', False)
            bfld = ui.BoolField(lidx=0, cidx=0, prefix='Bool', opt_var=bopt)
            conf_fields['bfld'] = bfld

            bopt2 = config.Bool('bool', False)
            bfld2 = ui.BoolField(
                lidx=0, cidx=20, prefix='Also Bool', opt_var=bopt2)
            conf_fields['bfld2'] = bfld2

            iopt = config.Int('int', 2, minval=1)
            ifld = ui.IntField(
                lidx=1, cidx=0, prefix='Ints', opt_var=iopt, suffix='mm',
                value_width=-6)
            conf_fields['ifld'] = ifld

            iopt2 = config.Int('int2', 10)
            ifld2 = ui.IntField(lidx=1, cidx=15, opt_var=iopt2)
            conf_fields['ifld2'] = ifld2

            copt = config.Choice('choice', choices=('one', 'two', 'three'))
            cfld = ui.ChoiceField(
                lidx=2, cidx=0, prefix='Choice', opt_var=copt)
            conf_fields['cfld'] = cfld
            panel = ui.ConfigPanel(conf_fields)

            buf = vpe.get_display_buffer(
                'test-config', buf_class=TestConfigView)
            buf.add_panel(panel)
        """
        self.run_self()

    @test(testID='cview-create')
    def create_a_config_view(self):
        """A config view may be created, using get_display_buffer.

        It will have one panel, which is accessible using the panels property.
        The configuration fields will be shown in the specified positions.

        :<py>:

            res = Struct()

            res.len_panels = len(buf.panels)
            res.change_count = buf.data.change_count
            res.lines = list(buf)
            dump(res)
        """
        self.setup_test_config_view()
        res = self.run_self()
        failUnlessEqual(1, res.len_panels)
        failUnlessEqual(0, res.change_count)
        failUnlessEqual('| Bool ( )            Also Bool ( )', res.lines[0])
        failUnlessEqual('| Ints      2mm  10    ', res.lines[1])
        failUnlessEqual('| Choice one  ', res.lines[2])
        sep_line = '`- Configuration -----------------------------------'
        sep_line += '---------------------------'
        failUnlessEqual(sep_line, res.lines[-1])

    @test(testID='cview-navigate')
    def navigate_a_config_view(self):
        r"""A config view's fields are navigated using the TAB key.

        TAB moves to the next field and Shift-TAB moves to the previous field.

        :<py>:

            res = Struct()

            panel = buf.panels[0]
            res.indices = [buf.data.field_idx]
            buf.show()
            vpe.feedkeys(r'\<C-\>\<C-N>\<Tab>')
        """
        self.setup_test_config_view()
        res = self.run_self()

        self.vs.execute_python_code(support.clean_code_block(r'''
            res.indices.append(buf.data.field_idx)
            vpe.feedkeys(r'\<Tab>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            res.indices.append(buf.data.field_idx)
            vpe.feedkeys(r'\<Tab>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            res.indices.append(buf.data.field_idx)
            vpe.feedkeys(r'\<Tab>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            res.indices.append(buf.data.field_idx)
            vpe.feedkeys(r'\<Tab>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            res.indices.append(buf.data.field_idx)
            vpe.feedkeys(r'\<S-Tab>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            res.indices.append(buf.data.field_idx)
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            dump(res)
        '''))

        res = self.result()
        failUnlessEqual([0, 1, 2, 3, 4, 0, 4], res.indices)

    @test(testID='cview-increment')
    def increment_fields(self):
        """A config view's fields can be incremented using <Space>.

        :<py>:

            # from functools import partial
            res = Struct()

            buf.show()
        """
        self.setup_test_config_view()
        res = self.run_self()

        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<C-\>\<C-N>\<Tab>\<Space>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<Tab>\<Space>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<Tab>\<Space>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<Tab>\<Space>\<Space>\<Space>\<Space>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<Tab>\<Space>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            res.lines = list(buf)
            dump(res)
        '''))

        res = self.result()
        failUnlessEqual('| Bool (x)            Also Bool (x)', res.lines[0])
        failUnlessEqual('| Ints      3mm  11    ', res.lines[1])
        failUnlessEqual('| Choice two  ', res.lines[2])
        sep_line = '`- Configuration -----------------------------------'
        sep_line += '---------------------------'

    @test(testID='cview-decrement')
    def decrement_fields(self):
        """A config view's fields can be decremented using <S-Space>.

        :<py>:

            res = Struct()

            buf.show()
            vpe.commands.redraw()
        """
        self.setup_test_config_view()
        res = self.run_self()

        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<Tab>\<S-Space>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<Tab>\<S-Space>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<Tab>\<S-Space>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<Tab>\<S-Space>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<Tab>\<S-Space>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            res.lines = list(buf)
            dump(res)
        '''))

        res = self.result()
        failUnlessEqual('| Bool (x)            Also Bool (x)', res.lines[0])
        failUnlessEqual('| Ints      1mm  9     ', res.lines[1])
        failUnlessEqual('| Choice three', res.lines[2])
        sep_line = '`- Configuration -----------------------------------'
        sep_line += '---------------------------'

    @test(testID='cview-edit')
    def edit_field(self):
        r"""A config view's fields can be edited using <Enter>.

        :<py>:

            res = Struct()

            buf.show()
            vpe.feedkeys(r'\<Tab>\<Enter>')
        """
        self.setup_test_config_view()
        res = self.run_self()

        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<Tab>\<Enter>')
        '''))
        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<BS>99\<Enter>')
        '''))
        self.vs.execute_python_code(support.clean_code_block('''
            res.lines = list(buf)
            dump(res)
        '''))

        res = self.result()
        failUnlessEqual('| Bool ( )            Also Bool ( )', res.lines[0])
        failUnlessEqual('| Ints     99mm  10    ', res.lines[1])
        failUnlessEqual('| Choice one  ', res.lines[2])
        sep_line = '`- Configuration -----------------------------------'
        sep_line += '---------------------------'

    @test(testID='cview-edit-bad')
    def edit_field_bad_value(self):
        r"""Invalid values are handled gracefully.

        :<py>:

            res = Struct()

            buf.show()
            vpe.feedkeys(r'\<C-\>\<C-N>\<Tab>\<Tab>\<Enter>')
        """
        self.setup_test_config_view()
        res = self.run_self()

        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<BS>Hello\<Enter>')
        '''))
        self.vs.execute_python_code(support.clean_code_block('''
            res.lines = list(buf)
            dump(res)
        '''))

        res = self.result()
        failUnlessEqual('| Bool ( )            Also Bool ( )', res.lines[0])
        failUnlessEqual('| Ints      2mm  10    ', res.lines[1])
        failUnlessEqual('| Choice one  ', res.lines[2])
        sep_line = '`- Configuration -----------------------------------'
        sep_line += '---------------------------'

    @test(testID='cview-edit-oor')
    def edit_field_oor_value(self):
        r"""Out of range values are handled gracefully.

        :<py>:

            res = Struct()

            buf.show()
            vpe.feedkeys(r'\<C-\>\<C-N>\<Tab>\<Tab>\<Enter>')
        """
        self.setup_test_config_view()
        res = self.run_self()

        self.vs.execute_python_code(support.clean_code_block(r'''
            vpe.feedkeys(r'\<BS>0\<Enter>')
        '''))
        self.vs.execute_python_code(support.clean_code_block('''
            res.lines = list(buf)
            dump(res)
        '''))

        res = self.result()
        failUnlessEqual('| Bool ( )            Also Bool ( )', res.lines[0])
        failUnlessEqual('| Ints      2mm  10    ', res.lines[1])
        failUnlessEqual('| Choice one  ', res.lines[2])
        sep_line = '`- Configuration -----------------------------------'
        sep_line += '---------------------------'


if __name__ == '__main__':
    runModule()
