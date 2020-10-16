"""Simple display and control panel framework."""


class CurPrev(int):
    """An value that knows its previous value."""
    def __init__(self, value):
        self._value = value
        self._prev = None
        self._changed = True

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._prev = self._value
        self._value = value

    @property
    def changed(self):
        return self._prev != self._value

    def restore_prev(self):
        self._value = self._prev
        return self._value


class Field:
    """A modifiable field within a panel."""
    active = True

    def __init__(self, lidx, cidx, label, *values, **kwargs):
        self.lidx = lidx
        self.cidx = cidx
        self.label = label
        self.values = values
        self.label_width = kwargs.pop('label_width', 0)
        init = kwargs.pop('init', None)
        try:
            self.index = self.values.index(init)
        except ValueError:
            self.index = 0
        self.__dict__.update(kwargs)

    @property
    def line_width(self):
        return self.cidx + self.width

    @property
    def width(self):
        return len(self.label) + len(':[]')

    @property
    def value(self):
        return self.values[self.index]

    @property
    def label_str(self):
        s = f'{self.label}:'
        if self.label_width:
            s = f'{s:<{self.label_width}}'
        return s

    def next(self):
        self.index += 1
        if self.index >= len(self.values):
            self.index = 0

    def prev(self):
        self.index -= 1
        if self.index < 0:
            self.index =  len(self.values) - 1

    def render(self, syn, selected=False):
        return f'{self.label}:'


class Label(Field):
    active = False


class BoolField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, True, False, **kwargs)

    def render(self, syn, selected=False):
        x = (' ', 'x')[self.value]
        if selected:
            return f'[({x}){self.label}]'
        return f' ({x}){self.label} '


class ChoiceField(Field):
    """A field holding one of a list of choices."""
    @property
    def val_width(self):
        return max(len(v) for v in self.values)

    @property
    def width(self):
        return super().width + self.val_width

    def render(self, syn, selected=False):
        if selected:
            return f'{self.label_str}[{self.value:<{self.val_width}}]'
        return f'{self.label_str} {self.value}'


class Panel:
    """Part of a display buffer."""
    def __init__(self):
        self.start_lidx = 0
        self.end_lidx = 0

    @property
    def lrange(self):
        return self.start_lidx, self.end_lidx

    def render(self, lidx, syn):
        self.start_lidx = lidx
        lines = self._render(lidx, syn)
        self.end_lidx = self.start_lidx + len(lines)
        self.gen_highlighting(syn)
        return lines

    def gen_highlighting(self, syn):
        pass

    def _render(self, lidx, syn):
        pass
