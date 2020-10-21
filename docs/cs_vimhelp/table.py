"""Paul's take on textual tables.

Mainly because I wish to support column spanning - eventually.
"""

from __future__ import annotations

from typing import List, Iterable
import itertools
import textwrap


class Grid:
    """A representation of a writable character grid."""
    def __init__(self):
        self.rows = []

    def write(self, x, y, text):
        while len(self.rows) < y + 1:
            self.rows.append('')
        line = self.rows[y]
        n = len(text)
        a, b = line[:x], line[x:]
        a = a.ljust(x)
        c = b[n:]
        self.rows[y] = a + text + c

    def __str__(self):
        return '\n'.join(self.rows)


class CascadedAttr:
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, _):
        v = getattr(obj, f'_{self.name}', None)
        return getattr(obj.parent, self.name) if v is None else v

    def __set__(self, obj, value):
        setattr(obj, f'_{self.name}', value)


class BorderedArea:
    def __init__(self, parent=None):
        self.parent = parent

    left_pad = CascadedAttr('left_pad')
    right_pad = CascadedAttr('left_pad')
    vert_border = CascadedAttr('vert_border')
    top_border = CascadedAttr('top_border')
    bottom_border = CascadedAttr('bottom_border')
    vertex = CascadedAttr('vertex')


class ColumnSpec:
    def __init__(self, parent, width, index):
        self.parent = parent
        self.width = width
        self.index = index

    left_pad = CascadedAttr('left_pad')
    right_pad = CascadedAttr('left_pad')


class Table(BorderedArea):
    """A structure representing the contents of a table."""
    def __init__(self, *, width_spec, **kwargs):
        super().__init__()
        self.c_specs = [
            ColumnSpec(self, w, i) for i, w in enumerate(width_spec)]
        self.cells = {}
        self._right_pad = self._left_pad = ' '
        self._vert_border = '|'
        self._top_border = '-'
        self._bottom_border = '-'
        self._vertex = '-'
        self.yvals = []

    @property
    def n_columns(self):
        return len(self.c_specs)

    @property
    def n_rows(self):
        return max(c.end_row for c in self.cells.values())

    def text_width(self, col, col_span):
        w = sum(c.width for c in self.c_specs[col: col + col_span])
        padlen = len(self.left_pad) + len(self.right_pad)
        return w + (col_span - 1) * (1 + padlen)

    def x(self, col):
        w = sum(c.width for c in self.c_specs[:col])
        return w + col * (1 + len(self.left_pad) + len(self.right_pad))

    def y(self, row):
        try:
            return self.yvals[row]
        except IndexError:
            y = 0
            for ri in range(row):
                y += 1 + self.row_height(ri)
            return y

    def _cols_width(self, cols):
        w = sum(c.width for c in cols)
        n = len(cols)
        return w + (n - 1) * (1 + len(self.left_pad) + len(self.right_pad))

    def add_cell(self, row, col, text='', row_span=1, col_span=1) -> Cell:
        cell = Cell(
            self, row, col, text=text, row_span=row_span, col_span=col_span)
        self.cells[(row, col)] = cell
        return cell

    def expand_columns(self, ci, span, alloc_w, fw):
        extra = fw - alloc_w
        widths = [cs.width for cs in self.c_specs[ci:ci + span]]
        while extra > 0:
            for i in range(span):
                if extra:
                    self.c_specs[ci + i].width += 1
                    extra -= 1
        new = [cs.width for cs in self.c_specs[ci:ci + span]]

    def adjust_widths(self, span):
        for c_spec, col in zip(self.c_specs, self.cols):
            col = [c for c in col if c.col_span == span]
            if col:
                fw = max(c.fw for c in col)
                alloc_w = self.text_width(c_spec.index, span)
                if fw > alloc_w:
                    self.expand_columns(c_spec.index, span, alloc_w, fw)

    def layout(self):
        for c in sorted(self.cells.values(), key=lambda c: (c.col, c.row)):
            c.layout()
        for span in range(1, self.n_columns):
            self.adjust_widths(span)
        for c in sorted(self.cells.values(), key=lambda c: (c.col, c.row)):
            c.layout()

    def render_grid(self):
        self.yvals = yvals = [0] * (self.n_rows + 1)
        for r in self.rows:
            for c in r:
                i, y = c.y_next()
                yvals[i] = max(yvals[i], y)

        grid = Grid()
        for r in self.rows:
            for c in r:
                c.render_grid(grid)
        return str(grid)

    def row_height(self, ri):
        row_cells = (c for k, c in self.cells.items() if k[0] == ri)
        return max(1, *[len(c.lines) for c in row_cells])

    @property
    def rows(self):
        # Create a set of default (empty) cells.
        rows = []
        for ri in range(self.n_rows):
            rows.append([Cell(self, ri, i) for i in range(self.n_columns)])

        # Replace entries with the actual cells, noting those to delete due to
        # spanning.
        todel = []
        for c in self.cells.values():
            rows[c.row][c.col] = c
            for ri, ci in itertools.product(
                    range(c.row_span), range(c.col_span)):
                if (ri, ci) != (0, 0):
                    todel.append((c.row + ri, c.col + ci))

        # Remove cells that are obscured by spanning.
        for ri, ci in reversed(todel):
            rows[ri].pop(ci)
        yield from rows

    @property
    def cols(self):
        yield from zip(*self.rows)

    def render(self):
        self.layout()
        return self.render_grid()


class Cell(BorderedArea):
    def __init__(self, table, row, col, text='', row_span=1, col_span=1):
        super().__init__(parent=table)
        self.row = row
        self.col = col
        self.text = text
        self.col_span = col_span
        self.row_span = row_span
        self.lines = [text]

    @property
    def text_width(self):
        return self.parent.text_width(self.col, self.col_span)

    @property
    def end_row(self):
        return self.row + self.row_span

    def layout(self):
        w = self.vw
        lines = textwrap.wrap(self.text, width=w, break_long_words=False)
        lines = [line.ljust(w) for line in lines]
        if not lines:
            self.lines = ['']
        self.lines = [line.ljust(w) for line in lines]

    def render_grid(self, grid):
        x, y = self.x, self.y
        lp, rp = self.left_pad, self.right_pad
        w = self.vw + len(lp) + len(rp)
        v = self.vertex
        grid.write(x, y, f'{v}{self.top_border * w}{v}')
        vert_border = self.vert_border
        for i, line in enumerate(self.vlines):
            line = line.ljust(self.vw)
            text = f'{vert_border}{lp}{line}{rp}{vert_border}'
            grid.write(x, y + i + 1, text)
        grid.write(x, y + i + 2, f'{v}{self.top_border * w}{v}')

    @property
    def vlines(self):
        h = self.parent.y(self.row + self.row_span) - self.y - 1
        n = len(self.lines)
        if n >= h:
            return self.lines
        return self.lines + [' ' * self.vw for _ in range(h - n)]

    @property
    def x(self):
        return self.parent.x(self.col)

    @property
    def y(self):
        return self.parent.y(self.row)

    def y_next(self):
        y_start = self.parent.y(self.row)
        y_end = y_start + len(self.lines) + 1
        return self.row + self.row_span, y_end

    @property
    def vw(self):
        return self.parent.text_width(self.col, self.col_span)

    @property
    def fw(self):
        return max(len(line) for line in self.lines)


if __name__ == '__main__':
    t = Table(width_spec=[7, 15, 10, 15])
    t.add_cell(0, 0, text='Column_1', col_span=1)
    # t.add_cell(0, 1, text='Column 2')
    # t.add_cell(0, 2, text='Column 3')
    t.add_cell(0, 3, text='Column 4')

    print()
    print('          1         2         3         4         5         6')
    print('0123456789'*7)

    # r.top_border = '='
    t.add_cell(1, 0, col_span=2, row_span=2, text='''Mainly because I wish to support column spanning.
Floccinaucinihilipilification.
Mainly because I wish to support column spanning.''')
    t.add_cell(1, 2, text='Paul ' * 5)
    t.add_cell(1, 3, text='Ollis')
    t.add_cell(2, 2, text='sid ' * 5)

    t.add_cell(3, 0, text='bert ' * 5)

    print(t.render())
    if 0:
        r[0].merge_right()
        # r[0].merge_right()

        r = t.add_row()
        r[0].text = 'One'
        r[1].text = 'Two'
        r[2].text = 'Three'
        r[3].text = 'Four'

        print()
        print(t.render())
