"""A simple buffer navigation plugin.

When executed this will setup <F4> to bring up the navigation window.
"""

import itertools
import re

from vpe import mapping, vim, commands, syntax
import vpe

from examples.vpe_panels import ChoiceField, Panel, BoolField, Label, CurPrev

NAV_STORE_NAME = 'vpe-nav'
NAV_BUF_NAME = 'buf-nav'
_hi_links = {
    'normal':  'Normal',
    'nofile':   'Comment ',
    'nowrite':  'Constant',
    'acwrite':  'Constant',
    'quickfix': 'Statement',
    'help':     'Special',
    'terminal': 'PreProc',
    'prompt':   'Type',
    'popup':    'Comment',
    'sel_field':  'IncSearch',
}
_short_help = '''
Press <F1> for help, q to quit.
'''
_long_help = '''
Press <F1> to hide help, q to quit.
<Tab>:   Move to next control panel field.
<Space>: Cycle choices for selected control panel field.
<Enter>: Open the currently highlighted buffer.
h:       Toggle showing hidden buffers.
l:       Toggle showing special (help, popup, etc.) buffers.
m:       Toggle showing unmodified buffers.
n:       Toggle showing unnamed buffers.
p:       Toggle splitting of file and path name
q:       Just close this navigator window.
r:       Reverse sort.
s:       Cycle through sort order choices.
S:       Reverse cylce through sort order choices.
-- Help ----------------------------------------------------------------------
'''


class Help(Panel):
    """The help part of the display."""
    def __init__(self):
        super().__init__()
        self.detailed = False

    def _render(self, lidx, syn):
        if self.detailed:
            return _long_help.splitlines()[1:]
        return _short_help.splitlines()[1:]

    def gen_highlighting(self, syn):
        help = syn.group('HelpToggle', link_to='Special')
        helpkey = syn.group('HelpKey', link_to='Special')
        title = syn.group('HelpTitle', link_to='Constant')
        help.add_match('^.*', lidx=self.start_lidx)
        if self.detailed:
            help.add_match('^.*', lidx=self.end_lidx - 1)
        helpkey.add_match(
            '^[^:]*', lrange=(self.start_lidx + 1, self.end_lidx))

    def toggle_detailed(self):
        self.detailed = not self.detailed


class Control(Panel):
    """The control part of the display."""
    def __init__(self):
        super().__init__()
        w = 16
        self.fields = {
            'order': ChoiceField(
                0, 0, 'Sort order', 'MRU', 'name', 'number', 'long name',
                label_width=w),
            'reversed': BoolField(0, w + 14, 'reversed', init=False),
            'disp_mode': ChoiceField(
                1, 0, 'Display name', 'split', 'full', label_width=w),
            'filter': Label(2, 0, 'Display filter'),
            'f_special': BoolField(2, w, 'special'),
            'f_hidden': BoolField(2, w + 12, 'hidden'),
            'f_unmodified': BoolField(2, w + 23, 'unmodified'),
            'f_unnamed': BoolField(2, w + 38, 'unnamed'),
        }
        self.index = 0

    def _render(self, lidx, syn):
        max_line = max((f.lidx for f in self.fields.values()), default=0) + 1
        lines = [''] * max_line
        lines.append('-- Control '.ljust(79, '-'))
        for fidx, f in enumerate(self.fields.values()):
            line = lines[f.lidx].ljust(f.line_width)
            a, b = line[:f.cidx], line[f.cidx + f.width:]
            lines[f.lidx] = a + f.render(syn, selected=fidx == self.index) + b
        return lines

    def gen_highlighting(self, syn):
        selected = syn.group('sel_field', link_to='IncSearch')
        panel = syn.group('control_panel', link_to='MoreMsg')
        sidx, eidx = self.start_lidx, self.end_lidx
        selected.add_match(r'\[[^]]\{-}\]', lrange=self.lrange)
        panel.add_match(r'^.\{16}', lrange=(sidx, eidx - 1))
        panel.add_match(r'^.*', lidx=self.end_lidx - 1)

    def handle_key(self, info):
        """Handle key press."""
        if info.keys == '<Tab>':
            start = self.index
            fields = list(self.fields.values())
            while True:
                self.index += 1
                if self.index >= len(self.fields):
                    self.index = 0
                if fields[self.index].active or start == self.index:
                    break
        elif info.keys == '<Space>':
            list(self.fields.values())[self.index].next()
        elif info.keys == '<S-Space>':
            list(self.fields.values())[self.index].prev()

    def setting(self, name):
        return self.fields[name].value


class BufStatus(Panel):
    """The general status part of the display."""
    def __init__(self, buf):
        super().__init__()
        self.buf = buf

    def _render(self, lidx, syn):
        return ['', '', '', '', '-- Details '.ljust(79, '-')]

    def gen_highlighting(self, syn):
        number = syn.group('value', link_to='Title')
        name = syn.group('name', link_to='Identifier')
        dirname = syn.group('dirname', link_to='Directory')
        special = syn.group('special', link_to='WarningMsg')
        panel = syn.group('details_panel', link_to='Comment')

        sidx, eidx = self.start_lidx, self.end_lidx
        name.add_match(r'^.\{17}\zs.*', lidx=sidx)
        dirname.add_match(r'^.\{17}\zs.*', lidx=sidx + 1)
        dirname.add_match(r'^.\{17}\zs.*', lidx=sidx + 1)
        special.add_match(r'Modified\ze,', lidx=sidx + 2)
        special.add_match(r'unlisted\ze,', lidx=sidx + 2)
        special.add_match(r'unloaded\ze,', lidx=sidx + 2)
        special.add_match(r'hidden\ze,', lidx=sidx + 2)
        number.add_match(r'\d\+', lrange=(sidx+2, sidx + 4))
        panel.add_match(r'^.\{16}', lrange=(sidx, eidx - 1))
        panel.add_match(r'^.*', lidx=self.end_lidx - 1)

    def update(self, entry):
        info = vim.getbufinfo(entry.number)[0]
        lines = [[] for _ in range(4)]
        s = lines[0]
        s.append(f'Number/name: {entry.number:<3} {entry.short_display_name}')
        s = lines[1]
        s.append(f'Location:        {entry.short_description}')
        s = lines[2]
        age = vim.localtime() - entry.lastused
        mod = 'modified' if entry.changed else 'unmodified'
        s.append(f'Status:          {mod}')
        s.append('listed' if entry.listed else 'unlisted')
        s.append('loaded' if entry.loaded else 'unloaded')
        s.append('hidden' if entry.hidden else 'active')
        s.append(f'line = {entry.lnum}/{entry.linecount}')
        s = lines[3]
        s.append(f'                 visible in {len(entry.windows)} windows')
        s.append(f'changedtick = {entry.changedtick}')
        s.append(f'last used {age}s ago')

        with self.buf.modifiable():
            for i, line in enumerate(lines):
                self.buf[self.start_lidx + i] = ', '.join(line)


class ListBufferEntry:
    """An entry in the list of buffers."""
    def __init__(self, buf, info):
        self.buf = buf
        self.flags = info['flags']

    def sortkey(self, order):
        if order == 'number':
            return self.buf.number
        elif order == 'name':
            return self.buf.short_display_name
        elif order == 'mru':
            if self.buf.name == '/[[buf-explore]]':
                return 1
            return -vim.getbufinfo(self.buf.number)[0]['lastused']
        return self.buf.name or self.buf.short_display_name

    def __getattr__(self, name):
        return getattr(self.buf, name)


class BufList(Panel):
    """The buffer list part of the display."""
    def __init__(self, control, status):
        super().__init__()
        self.control = control
        self.status = status
        self.row = CurPrev(0)
        self.sel_buf_number = 0
        self.empty = False

    def _get_buflist(self):

        def filtered(entry):
            if entry.hidden and not fields['f_hidden'].value:
                return False
            if entry.type != 'normal' and not fields['f_special'].value:
                return False
            if not entry.options.modified and not fields['f_unmodified'].value:
                return False
            if (entry.short_display_name
                    == '[No name]' and not fields['f_unnamed'].value):
                return False
            return True

        fields = self.control.fields
        info = get_ls_info()
        buflist = sorted(
            [ListBufferEntry(buf, info[buf.number]) for buf in vim.buffers],
            key=lambda b: b.sortkey(self.control.setting('order')),
            reverse=self.control.fields['reversed'].value)
        self._buflist = [entry for entry in buflist if filtered(entry)]

    def _render(self, lidx, syn):
        """Update the list of buffers."""

        def format_buf_line():
            if self.control.setting('disp_mode') == 'full':
                name = entry.long_display_name
                return f'{entry.number:>3} {entry.flags}: {name}'
            name = entry.short_display_name
            dname = entry.short_description
            return f'{entry.number:>3} {entry.flags}: {name:<{w}} {dname}'

        self._get_buflist()
        lines = []
        w = max(8, *(len(buf.short_display_name) for buf in vim.buffers))
        for i, entry in enumerate(self._buflist):
            lines.append(format_buf_line())
            btype = entry.type
            grp = syn.group(btype, link_to=_hi_links[btype])
            grp.add_match(r'^.\{,4\}\zs.*$', lidx=len(lines) + lidx - 1)
        if not lines:
            lines.append('<<< No buffers to display >>>')
            self.empty = True
        else:
            self.empty = False
        return lines

    def set_initial_line(self):
        i = 0
        if not self.empty:
            for i, entry in enumerate(self._buflist):
                if entry.number == self.sel_buf_number:
                    break
        vim.cursor(self.start_lidx + 1 + i, vim.col('.'))

    def handle_cursor_moved(self):
        """Handle cursor movement by constraining line range."""
        self.row.value, c = vim.line('.'), vim.col('.')
        if self.row.changed and self.row.value <= self.start_lidx:
            vim.cursor(self.row.restore_prev(), c)
        if not self.empty:
            entry = self._buflist[self.row.value - self.start_lidx - 1]
            self.sel_buf_number = entry.number
            self.status.update(entry)


class BufView:
    """The entire view of buffer navigator."""
    def __init__(self):
        self.buf = vpe.get_display_buffer(NAV_BUF_NAME)
        self.control = Control()
        self.status = BufStatus(self.buf)
        self.buf_list = BufList(self.control, self.status)
        self.help = Help()
        self.layout = self.help, self.control, self.status, self.buf_list
        self.config_handle_func = {
            'p': self.control.fields['disp_mode'].next,
            'r': self.control.fields['reversed'].next,
            's': self.control.fields['order'].next,
            'S': self.control.fields['order'].prev,
            'h': self.control.fields['f_hidden'].next,
            'l': self.control.fields['f_special'].next,
            'm': self.control.fields['f_unmodified'].next,
            'n': self.control.fields['f_unnamed'].next,
            '<F1>': self.help.toggle_detailed,
        }

    def run(self, _info=None):
        """Bring up the buffer view using a split window."""
        buf = self.buf
        if not buf.goto_active_window():
            buf.show(splitlines=3)
        vim.current.window.options.cursorline = True
        self.render()
        self.setup_event_handling()
        self.prev_line = self.buf_list.start_lidx + 1
        vim.cursor(self.prev_line, 1)

    def render(self):
        with self.buf.list() as lines, syntax.Syntax('buf_nav_') as syn:
            lines[:] = []
            for panel in self.layout:
                lines.extend(panel.render(lidx=len(lines), syn=syn))
        self.buf_list.set_initial_line()

    def setup_event_handling(self):
        """Set up handling of interesting events."""
        with vpe.AutoCmdGroup('VpeBufNav') as grp:
            grp.delete_all()
            grp.add('CursorMoved', self.buf_list.handle_cursor_moved)

        for key in ('<CR>', 'q'):
            mapping.nmap(key, func=self.handle_end_key)
        for key in ('<Tab>', '<Space>', '<S-Space>'):
            mapping.nmap(key, func=self.handle_control_key)
        for key in self.config_handle_func:
            mapping.nmap(key, func=self.handle_key)

    def handle_end_key(self, info):
        """Handle key press that will close the navigation window."""
        buf = None
        if info.keys == '<CR>':
            try:
                buf = vim.buffers[self.buf_list.sel_buf_number]
            except ValueError:
                pass
        commands.wincmd('c')
        if buf is not None:
            commands.buffer(buf.number)

    def handle_control_key(self, info):
        """Handle a control pane key."""
        self.control.handle_key(info)
        self.render()

    def handle_key(self, info):
        """Handle key press that affects the navigation configuration."""
        self.config_handle_func[info.keys]()
        self.render()


def get_ls_info():
    """Use the ':ls' command to get information about the buffers.

    This is a straighforward way to get the flags (%+- etc.).
    """
    r_info = re.compile(r'''(?x)
        \s *                        # Optional leading space
        (?P<number>\d+)             # Buffer number
        (?P<flags>
            (?P<unlisted>.)             # The u flag.
            (?P<cur_alt>.)              # The %# flags.
            (?P<active>.)               # The ah flags.
            (?P<special>.)              # The -=RF? flags.
            (?P<modified>.)             # The +x flags.
        )
        \s* "(?P<disp_name>.*)"      # The buffer's display name
        \s* line \s \d+             # Current line number
        ''')
    info = vim.execute(':ls!').splitlines()
    matches = [r_info.match(line) for line in info]
    matches = [(int(m.group('number')), m) for m in matches if m]
    return  {n: m.groupdict() for n, m in matches}


def run():
    """Entry point for this example plugin."""
    buf = vpe.get_display_buffer(NAV_BUF_NAME)
    info = buf.store(NAV_STORE_NAME)
    bufview = info.bufview
    if bufview is None:
        bufview = BufView()
        mapping.nmap('<F4>', func=bufview.run, buffer=False)
        info.bufview = bufview
    bufview.run()
