"""Window specific support.

This provides support for working with Vim window layouts. The intended way to
use this is to use `LayoutElement.create_from_vim_layout`. For example:<py>:

    layout = LayoutElement.create_from_vim_layout(vim.winlayout())

The returned value will be a `LayoutRow`, `LayoutColumn` or `LayoutWindow`
window instance. Use the `type_name` class attribute when it is necessary to
know the actual type.
"""

from typing import List

from vpe import commands, vim


class LayoutElement:
    """An element in a window layout.

    Each element is either a LayoutRow, LayoutColumn or a LayoutWindow.

    @type_name: A class attribute used to identify the type of element.
    """
    id = None
    type_name = ''
    width = 0

    def __init__(self, elements: List):
        self.children = [
            LayoutElement.create_from_vim_layout(entry) for entry in elements]

    @classmethod
    def create_from_vim_layout(cls, layout):
        """Create LayoutElement from the result of a winlayout() call."""
        name, element = layout
        if name == 'col':
            return LayoutColumn(element)
        if name == 'row':
            return LayoutRow(element)
        return LayoutWindow(element)

    def describe(self, level=0):
        """Generate a description as a sequence of lines.

        The description is intended to be user friendly. It is best not to rely
        on its format because it may change in future releases.
        """
        s = [f'{self.type_name} = {self.width}']
        for child in self.children:
            for line in child.describe(level=level + 1):
                s.append(f'    {line}')
        return s

    def set_widths_from_layout(self, layout: 'LayoutElement'):
        """Update the widths using another layour element.

        :layout: The `LayoutElement` to copy from.
        """
        widths = {win.id: win.width for win in layout.iter_windows()}
        for win in self.iter_windows():
            if win.id in widths:
                win.adjust_width(widths[win.id])

    def iter_windows(self):
        """Iterate through the leaf windows."""
        if self.type_name == 'Win':
            yield self
        else:
            for child in self.children:
                yield from child.iter_windows()

    def apply_sizes(self):
        """Apply this layout's sizes to the actual Vim window layout."""
        for win in self.iter_windows():
            commands.resize(
                win.width, a=vim.win_id2win(win.id), vertical=True)

    def __getitem__(self, idx: int):
        return self.children[idx]

    def __len__(self):
        return len(self.children)


class LayoutRow(LayoutElement):
    """Details of a row in a window layout.

    :row: A list of Vim column or leaf specs.
    """
    type_name = 'Row'

    @property
    def width(self):
        """The width of this row."""
        child_sum = sum(child.width for child in self.children)
        return child_sum + len(self.children) - 1

    def adjust_width(self, tot_width: int):
        """Adjust widths of children to match a new total width."""
        if tot_width == self.width:
            return
        len_borders = len(self.children) - 1
        cur_width = self.width
        proportions = [child.width / cur_width for child in self.children]
        new_widths = [max(1, int(p * tot_width + 0.5)) for p in proportions]
        new_width = sum(new_widths) + len_borders
        while new_width > tot_width:
            m = max(new_widths)
            if m == 1:
                break                                        # pragma: no cover
            new_widths[new_widths.index(m)] -= 1
            new_width = sum(new_widths) + len_borders
        while new_width < tot_width:
            m = min(new_widths)
            new_widths[new_widths.index(m)] += 1
            new_width = sum(new_widths) + len_borders

        for child, width in zip(self.children, new_widths):
            child.adjust_width(width)


class LayoutColumn(LayoutElement):
    """Details of a column in a window layout.

    :row: A list of Vim row or leaf specs.
    """
    type_name = 'Col'

    @property
    def width(self):
        """The width of this column."""
        return max(child.width for child in self.children)

    def adjust_width(self, tot_width: int):
        """Adjust widths of children to match a new total width."""
        if tot_width == self.width:
            return
        for child in self.children:
            child.adjust_width(tot_width)


class LayoutWindow(LayoutElement):
    """Details of a window in a window layout.

    :wid: The unique ID of the window.
    """
    type_name = 'Win'

    def __init__(self, win_id: int):
        super().__init__([])
        self.id = win_id
        self.number = vim.win_id2win(win_id)
        self._width = vim.winwidth(win_id)

    @property
    def width(self):
        """The width of this window."""
        return self._width

    def adjust_width(self, tot_width: int):
        """Adjust width of this window."""
        self._width = tot_width

    def describe(self, level=0):
        """Generate a description as a sequence of lines."""
        return [f'Win[{self.number}] = {self.width}']

    def __len__(self):
        return 1
