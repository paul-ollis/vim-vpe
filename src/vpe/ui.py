"""User interface components.

This is still being developed. The API and behaviour is likely to change.
"""

from typing import Any, Iterator, List, Tuple

import vpe
from vpe import mapping, panels, syntax, vim

SEL_HL = 'MatchParen'
SUFFIX_HL = 'Comment'
PREFIX_HL = 'Identifier'
BORDER_HL = 'Constant'


def format_str(s: str, width: int) -> str:
    """Format a string within a given field width.

    The string is truncated (if necessary) to the *width* and then left or
    right justified within the *width*. A *width* of zero results in an empty
    string.

    :s:     The string to justify.
    :width: The field width. Positive values mean left justified, negative mean
            right justified.
    """
    if width > 0:
        return s.ljust(width)
    if width < 0:
        return s.rjust(width)
    return ''


class CurPrev(int):                                          # pragma: no cover
    """An value that knows its previous value."""
    def __init__(self, value):
        super().__init__(value)
        self._value = value
        self._prev = None
        self._changed = True

    @property
    def value(self):
        """The current value."""
        return self._value

    @value.setter
    def value(self, value):
        self._prev = self._value
        self._value = value

    @property
    def changed(self) -> bool:
        """Whether this value has been changed."""
        return self._prev != self._value

    def restore_prev(self):
        """Restore this to its previous value.."""
        self._value = self._prev
        return self._value


class FieldVar:
    """A value that is displayed by a Field.

    This class defines the protocol that a `Field` uses to access its
    underlying value.
    """
    def __init__(self, _var):
        """Initialisation."""

    @property
    def value(self):
        """"The current value for this variable."""

    def set(self, _value: Any) -> str:
        """Try to set this option's value.

        :return: A string describing why the attempt failed. An empty string
                 if the value was set. This basic wrapper always returns an
                 empty string.
        """
        return ''                                            # pragma: no cover

    def values(self) -> List[Any]:
        """Return a set of the valid values for this field.

        :return: A list of the valid values. An empty list means that this
                 field's range of values is not defined using a set.
        """
        return []                                            # pragma: no cover


class Field:                     # pylint: disable=too-many-instance-attributes
    """Base class for a field within a `ConfigPanel`.

    A field consists of 3 parts; prefix, value and suffix. They are laid out
    like this (in this example the prefix and value are left justified and the
    suffix is right justified).
    ::

      |        prefix      value          suffix
      |        :          ::        ::         :
      |        :          ::        :<--------->  suffix_fmt_width
      |        <---------->:        :          :  prefix_fmt_width
      |        :           <-------->          :  val_extent[1] / value_width
      |        <------------------------------->  full_width
       ^       ^           ^
       :       :           `--------------------  val_extent[0]
       :       `--------------------------------  cidx
       `----------------------------------------  <buffer column zero>

    Note that full_width == prefix_fmt_width + value_width + suffix_fmt_width.

    :@lidx:         The line index within the panel.
    :@cidx:         The column index within the panel.
    :@prefix:       The label displayed before the field.
    :@suffix:       The label displayed after the field.
    :@prefix_width: The width spec for the prefix. If not provided then this
                    defaults to the width of the prefix + 1. If set to a
                    negative number, the prefix is right justified.
    :@suffix_width: The width spec for the prefix. It follows the same pattern
                    as the prefix_width.
    :value_width:   The width spec for the value. It follows the same pattern
                    as the prefix_width.
    """
    active = True
    default: Any = ''

    def __init__(                          # pylint: disable=too-many-arguments
            self, *, lidx, cidx, prefix='', suffix='', prefix_width=0,
            suffix_width=0, value_width=6, opt_var=None, **kwargs):
        self.lidx = lidx
        self.cidx = cidx
        self.prefix = prefix
        self.suffix = suffix
        self.prefix_width = prefix_width or (len(prefix) + 1 if prefix else 0)
        self.suffix_width = suffix_width or (len(suffix) if suffix else 0)
        self._value_width = value_width
        self._value = opt_var
        self.__dict__.update(kwargs)

    @property
    def value_width(self) -> int:
        """The width used to display the field's value."""
        return self._value_width

    @property
    def full_width(self) -> int:
        """The full width occupied by this field."""
        w = self.prefix_fmt_width + self.value_fmt_width
        return w + self.suffix_fmt_width

    @property
    def column_range(self) -> Tuple[int, int]:
        """The range of columns occupied by this field."""
        return self.cidx, self.cidx + self.full_width

    @property
    def value(self) -> Any:
        """The field's current value."""
        return self._value.store_value

    @property
    def value_str(self):
        """Format the value as a string."""
        # TODO: Should the _value provide a str() method!
        s = str(self.value)
        if self.value_width > 0:
            return s.ljust(self.value_width)
        if self.value_width < 0:
            return s.rjust(-self.value_width)
        return s                                             # pragma: no cover

    @property
    def value_fmt_width(self) -> int:
        """The width of this field's formatted value."""
        if self.value_width:
            return abs(self.value_width)
        return 0                                             # pragma: no cover

    @property
    def prefix_fmt_width(self) -> int:
        """The width of this field's formatted prefix."""
        if self.prefix_width:
            return abs(self.prefix_width)
        return 0

    @property
    def suffix_fmt_width(self) -> int:
        """The width of this field's formatted suffix."""
        if self.suffix_width:
            return abs(self.suffix_width)
        return 0

    @property
    def val_extent(self) -> Tuple[int, int]:
        """The extent of this field's value.

        :return: A tuple of cnum, width.
        """
        return self.cidx + self.prefix_fmt_width + 1, self.value_width

    def text(self) -> str:
        """Format the full text of the field."""
        lhs = format_str(self.prefix, self.prefix_width)
        rhs = format_str(self.suffix, self.suffix_width)
        v_str = format_str(self.value_str, self.value_width)
        return ''.join((lhs, v_str, rhs))

    def increment(self, _step: int) -> bool:
        """Increment this field's value by a given step.

        This typically needs to be over-ridden by subclasses.

        :return: True if the value was modified.
        """
        return False                                         # pragma: no cover

    def edit_value(self) -> bool:
        """Allow the user to edit the value of a field.

        This typically needs to be over-ridden by subclasses.

        :return: True if the value was modified.
        """
        return False


class BoolField(Field):
    """A field displaying a boolean value."""

    @property
    def value_width(self):
        return 3

    @property
    def value_str(self):
        return ('( )', '(x)')[self.value]

    def increment(self, _step: int) -> bool:
        """Increment this field's value by a given step."""
        self._value.set(not self.value)
        self._value.copy_to_store()
        return True


class IntField(Field):
    """A field displaying an integer value."""

    def increment(self, step: int) -> bool:
        self._value.set(self.value + step)
        self._value.copy_to_store()
        return True

    def edit_value(self) -> bool:
        """Allow the user to edit the value of a field.

        :return: True if the value was modified.
        """
        v_str = vim.input('Set value: ', self.value_str.strip())
        try:
            v = int(v_str)
        except ValueError:
            vpe.error_msg(
                f'Not an integer ({v_str}), value unchanged.', soon=True)
        else:
            if v != self.value:
                m = self._value.set(v)
                if m:
                    vpe.error_msg(m, soon=True)
                    return False
                self._value.copy_to_store()
                return True
        return False


# TODO: This is a bit messy and I am not sure whether supporting not using
#       opt_var is a good idea. Currentlym the _value argument is not used
#       so the opt_var is effectively mandatory.
class ChoiceField(Field):
    """A field holding one of a list of choices.

    ::values: A sequence of permitted values for the field. This is ignored.
    """
    def __init__(self, _values=(), opt_var=None, **kwargs):
        super().__init__(opt_var=opt_var, **kwargs)
        self._values = opt_var.values()
        self._value_index = self._value.index()
        self._value.set(self._values[self._value_index])
        if self._values:
            self._value_width = max(len(v) for v in self._values)

    @property
    def value_width(self):
        return max(len(v) for v in self._values)

    def increment(self, step: int):
        """Increment this field's value by a given step."""
        step = step // abs(step)
        self._value_index += step
        if self._value_index >= len(self._values):
            self._value_index = 0
        elif self._value_index < 0:
            self._value_index = len(self._values) - 1
        self._value.set(self._values[self._value_index])
        self._value.copy_to_store()
        return True


class ConfigPanel(panels.Panel):
    """A panel that displays configuration values.

    :@fields: The fields within this panel. A mapping from name to `Field`.

    @first_field_idx:
        The global index of the first field in this panel.
    @selectable_fields:
        A mapping from global field index to `Field` instance.
    """
    def __init__(self, fields):
        super().__init__()
        self.fields = fields
        self.selectable_fields = {}
        self.first_field_idx = 0
        self._selected_field = -1
        self._syn_groups = []

        # Increase all column indices by 2 to allow for the border.
        for field in self.fields.values():
            field.cidx += 2

    def index_fields(self, start_idx: int):
        """Set up the mapping from field index to field."""
        self.selectable_fields.clear()
        self.first_field_idx = start_idx
        for field in self.fields.values():
            if field.active:
                fidx = len(self.selectable_fields) + start_idx
                self.selectable_fields[fidx] = field
        return start_idx + len(self.selectable_fields)

    def select_field(self, index: int):
        """Select a specific field."""
        field = self.get_field_by_idx(index)
        if field:
            lnum = self.start_lidx + field.lidx + 1
            cnum, width = field.val_extent
            pat = rf'/\%{lnum}l\%{cnum}c.\{{{width}}}/'
            vpe.commands.match(SEL_HL, pat)

    def get_field_by_idx(self, index: int):
        """Get the editable field with a given index."""
        fidx = index - self.first_field_idx
        if 0 <= fidx < len(self.selectable_fields):
            return self.selectable_fields[index]
        return None                                          # pragma: no cover

    def apply_syntax(self):
        """Apply syntax highlighting for this panel.

        This is only called when the panel's `start_lidx` is correctly set.
        """
        with syntax.Syntax(self.syntax_prefix, clear=False) as syn:
            prefix = syn.group('prefix', link_to=PREFIX_HL)
            suffix = syn.group('suffix', link_to=SUFFIX_HL)
            border = syn.group('border', link_to=BORDER_HL)
            for field in self.fields.values():
                cidx, e_cidx = field.column_range
                lidx = self.start_lidx + field.lidx
                pw = field.prefix_fmt_width
                if pw:
                    prefix.add_match(fr'\%{cidx + 1}c.\{{{pw}}}', lidx=lidx)
                sw = field.suffix_fmt_width
                if sw:
                    suffix.add_match(
                        fr'\%{e_cidx - sw + 1}c.\{{{sw}}}', lidx=lidx)
            a, b = self.start_lidx, self.start_lidx + len(self.content)
            border.add_match('^.', lrange=(a, b))
            border.add_match(r'-\+', lidx=b - 1)

    def on_format_contents(self):
        """Refresh to formatted lines for this panel."""
        n_lines = max((f.lidx for f in self.fields.values()), default=0) + 1
        lines = [''] * n_lines
        lines.append('`- Configuration '.ljust(79, '-'))
        for field in self.fields.values():
            cidx, end_cidx = field.column_range
            text = field.text()
            lidx = field.lidx
            line = lines[lidx].ljust(end_cidx)
            lines[lidx] = line[:cidx] + text + line[end_cidx:]

        lines[:n_lines] = [f'| {line[2:]}' for line in lines[:n_lines]]
        self.content[:] = lines


class ConfigPanelBuffer(
        panels.PanelViewBuffer, mapping.KeyHandler, vpe.BufEventHandler):
    """A `PanelViewBuffer` that supports configuration panels.

    This tracks instances of `ConfigPanel` and sets up key mappings to navigate
    and modify the fields within them.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data.field_idx = 0
        self.data.field_index_range = 1

    def on_reindex(self):
        """Perform special processing when line reindexing has occurred."""
        super().on_reindex()
        index = 0
        for p in self.config_panels():
            index = p.index_fields(index)
        self.data.field_index_range = index

    def on_updates_applied(self, changes_occurred: bool):
        """Perform special processing when buffer has been refreshed.

        When this is invoked, this buffer may not be in the active window
        and my even be hidden.
        """
        self._highlight_selected_field()

    def _highlight_selected_field(self):
        """Set the highlighting for the selected field."""
        windows = self.find_active_windows()
        if windows:
            for window in windows:
                with vpe.temp_active_window(window):
                    for panel in self.config_panels():
                        panel.select_field(self.data.field_idx)
            return

        key = self._highlight_selected_field
        self.schedule_win_op(key, self._highlight_selected_field)

    @vpe.BufEventHandler.handle('BufWinEnter')
    @mapping.KeyHandler.mapped('normal', '<S-Tab>', args=(-1,))
    @mapping.KeyHandler.mapped('normal', '<Tab>',  args=(1,))
    def move_field(self, step: int = 0):
        """Move to a different field.

        :step: Increment for the field index.
        """
        self.data.field_idx += step
        self.data.field_idx %= self.data.field_index_range
        self._highlight_selected_field()
        self.on_selected_field_change()

    @mapping.KeyHandler.mapped('normal', '<S-Space>', args=(-1,))
    @mapping.KeyHandler.mapped('normal', '<Space>', args=(1,))
    def inc_field(self, step: int):
        """Increment the value in a field.

        :step: Value to change the field by. May be a negative value.
        """
        panel, field = self.get_field_by_idx(self.data.field_idx)
        if field:
            if field.increment(step):
                self.format_panel(panel)
                self.on_change()

    @mapping.KeyHandler.mapped('normal', ('<CR>', '<Return>'))
    def edit_field(self):
        """Allow the user to edit the value of a field."""
        panel, field = self.get_field_by_idx(self.data.field_idx)
        if field:
            if field.edit_value():
                self.format_panel(panel)
                self.on_change()

    def get_field_by_idx(self, index: int):
        """Get the editable field with a given index."""
        for panel in self.config_panels():
            field = panel.get_field_by_idx(index)
            if field:
                return panel, field
        return None, None                                    # pragma: no cover

    def config_panels(self) -> Iterator[ConfigPanel]:
        """Interate over all the configuration panels."""
        for panel in self.panels:
            if isinstance(panel, ConfigPanel):
                yield panel

    def on_change(self):
        """Perform common processing when value is changed.

        This is intended to be over-ridden by subclasses.
        """

    def on_selected_field_change(self):
        """Perform common processing when the selected field is changed.

        This is intended to be over-ridden by subclasses.
        """
