"""A pythonic API for creating syntax highlighting definitions."""

import functools
import weakref

import vpe
from vpe import commands


class SyntaxBase:
    _match_options = {
        'contains': lambda v: 'f={v}',
        'display': lambda v: '',
        'extend': lambda v: '',
        'fold': lambda v: '',
    }
    _region_options = {
        'concealends': lambda v: '',
        'contains': lambda v: 'f={v}',
        'display': lambda v: '',
        'extend': lambda v: '',
        'extend': lambda v: '',
        'fold': lambda v: '',
    }
    _other_options = {
        'cchar': lambda v: 'f={v}',
        'conceal': lambda v: '',
        'contained': lambda v: '',
        'containedin': lambda v: 'f={v}',
        'nextgroup': lambda v: 'f={v}',
        'skipempty': lambda v: '',
        'skipnl': lambda v: '',
        'skipwhite': lambda v: '',
        'transparent': lambda v: '',
    }
    _match_offset_names = set(('ms', 'me', 'hs', 'he'))

    def _format_options(self, options, supported):
        s = []
        for name, value in options.items():
            if value:
                fmt = supported.get(name, self._other_options.get(name))
                s.append(f'{name}{fmt(value)}')
        return tuple(s)

    def get_offsets(self, options, offset_names):
        offsets = ','.join(
            f'{n}={v}' for n, v in options.items() if n in offset_names)
        options = {n: v for n, v in options.items() if n not in offset_names}
        return offsets, options


class Option:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def vim_fmt(self):
        if self.value:
            return f'{self.name}'
        return ''


class Contains(Option):
    name = 'contains'

    def __init__(self, *groups):
        self.groups = []
        for g in groups:
            if isinstance(g, tuple):
                self.groups.extend(g)
            else:
                self.groups.append(g)

    def vim_fmt(self):
        if not self.groups:
            return ''
        args = ','.join(g.arg_name for g in self.groups)
        return f'{self.name}={args}'


class MatchGroup(Option):
    name = 'matchgroup'

    def __init__(self, group):
        self.group = group

    def vim_fmt(self):
        return f'{self.name}={self.group.qual_name}'



class Syntax(SyntaxBase):
    """Context manager for defining syntax highlighting.

    This stores a sequence of syntax highlighting directives. The directives
    are applied when the context is exited.
    """
    def __init__(self, group_prefix):
        self.prefix = group_prefix
        self._match_options['contains'] = self._expand_groups_arg
        self.groups = {}
        self.std_groups = {}
        self.clusters = {}

    def std_group(self, name):
        if name not in self.std_groups:
            self.std_groups[name] = Group(self, name, std=True)
        return self.std_groups[name]

    def group(self, name):
        if name not in self.groups:
            self.groups[name] = Group(self, name)
        return self.groups[name]

    def cluster(self, name):
        if name not in self.clusters:
            self.clusters[name] = Cluster(self, name)
        return self.clusters[name]

    def region(self, group, pat, **options):
        pass

    def fmt_group(self, name):
        if name.startswith('@'):
            return f'@{self.prefix}{name[1:]}'
        return f'{self.prefix}{name}'

    def fmt_groups(self, v):
        if isinstance(v, str):
            names = v.split(',')
        else:
            names = v
        return ','.join(f'{self.fmt_group(name)}' for name in names)

    def _expand_groups_arg(self, v):
        return f'={self.fmt_groups(v)}'

    def schedule(self, func, *args, **kwargs):
        self._directives.append((func, args, kwargs))

    def preview_last(self):
        func, args, kwargs = self._directives[-1]
        return func(*args, **kwargs, preview=True)

    def __enter__(self):
        self._directives = [(commands.syntax, ('clear',), {})]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for func, args, kwargs in self._directives:
            func(*args, **kwargs)
        for cluster in self.clusters.values():
            cluster.invoke()
        for group in self.groups.values():
            group.invoke()
        for group in self.std_groups.values():
            group.invoke()


class NamedSyntaxItem(SyntaxBase):

    def __init__(self, syn, name, std=False):
        self.syn = weakref.proxy(syn)
        self._name = name
        self._std = std

    @property
    def name(self):
        return self._name

    @property
    def qual_name(self):
        if self._std:
            return self._name
        return self.syn.fmt_group(self._name)

    @property
    def arg_name(self):
        return self.qual_name


class Group(NamedSyntaxItem):

    def __init__(self, syn, name, std=False):
        super().__init__(syn, name, std=std)
        self.linked = set()

    def add_links(self, *groups):
        """Add groups to the sent that lnk to this group."""
        for group in groups:
            if isinstance(group, str):
                group = self.syn.group(group)
            self.linked.add(group)

    def add_match(self, *pat, lidx=None, lrange=None, **options):
        """Add a syntax match for this group."""
        pats = list(pat)
        offsets, options = self.get_offsets(options, self._match_offset_names)
        if lidx is not None:
            pats[0:0] =  [fr'\%{lidx + 1}l']
        elif lrange is not None:
            a, b = lrange
            prefix = ''
            if a is not None:
                prefix += fr'\%>{a}l'
            if b is not None:
                prefix += fr'\%<{b + 1}l'
            pats[:] =  [prefix]
        pat = ''.join(pats)
        self.syn.schedule(
            commands.syntax, 'match', f'{self.qual_name}', f'"{pat}"{offsets}',
            *self._format_options(options, self._match_options, ))

    def add_region(self, *, start=None, skip=None, end=None, **options):
        """Add a syntax region for this group.

        This is only suitable for simple region definitions. Only a single
        start, skip and end pattern can be added. For more complex cases use
        a `region` context.
        """
        with Region(self.syn, self.qual_name, *options) as region:
            if start:
                region.start(start)
            if skip:
                region.skip(skip)
            if end:
                region.end(end)

    def region(self, **options):
        """Create a region context manager.

        This supports regions with multiple start, skip and end patterns.
        """
        return Region(self.syn, self.qual_name, **options)

    def highlight(self, **kwargs):
        """Define highlighting for this group.

        :kwargs:
            These are the same as for `vpe.highlight`, except that ``group``
            and ``clear`` should not be  used.
        """
        vpe.highlight(group=self.qual_name, **kwargs)

    def invoke(self):
        hilink = functools.partial(
            commands.highlight, 'default', 'link', bang=True)
        for group in self.linked:
            hilink(group.qual_name, self.qual_name)

    match = add_match


def convert_syntax_options(options):
    for name in options:
        if name == 'contains':
            options[name] = Contains(options[name])
        elif name == 'matchgroup':
            options[name] = MatchGroup(options[name])
        else:
            options[name] = Option(name, options[name])
    return options


class Region(SyntaxBase):
    _options = {
        'concealends': lambda v: '',
        'contains': lambda v: 'f={v}',
        'display': lambda v: '',
        'extend': lambda v: '',
        'extend': lambda v: '',
        'fold': lambda v: '',
    }

    def __init__(self, syn, name, **options):
        self.syn = syn
        self.qual_name = name
        self.starts, self.skips, self.ends = [], [], []
        self.preview = options.pop('preview', False)
        self.options = convert_syntax_options(options)

    def start(self, *pat, **kwargs):
        self.starts.append(Start(''.join(pat), **kwargs))
        return self

    def skip(self, *pat, **kwargs):
        self.skips.append(Skip(''.join(pat), **kwargs))
        return self

    def end(self, *pat, **kwargs):
        self.ends.append(End(''.join(pat), **kwargs))
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.syn.schedule(
                commands.syntax, 'region', f'{self.qual_name}',
                *[p.arg_str() for p in self.starts],
                *[p.arg_str() for p in self.skips],
                *[p.arg_str() for p in self.ends],
                *[opt.vim_fmt() for opt in self.options.values()])
            if self.preview:
                print(self.syn.preview_last())


class Pattern(SyntaxBase):

    def __init__(self, pat, lidx=None, lrange=None, **options):
        self.pat = pat
        self.matchgroup = options.pop('matchgroup', None)
        self.offsets, _ = self.get_offsets(options, self._offset_names)
        if lidx is not None:
            self.pat =  fr'\%{lidx + 1}l' + pat
        elif lrange is not None:
            a, b = lrange
            prefix = ''
            if a is not None:
                prefix += fr'\%>{a}l'
            if b is not None:
                prefix += fr'\%<{b + 1}l'
            self.pat =  prefix + pat

    def arg_str(self):
        s = []
        if self.matchgroup:
            s.append(f'matchgroup={self.matchgroup.qual_name}')
        s.append(f'{self._name}="{self.pat}"{self.offsets}')
        return ' '.join(s)


class Start(Pattern):
    _offset_names = set(('ms', 'hs', 'rs'))
    _name = 'start'


class Skip(Pattern):
    _offset_names = set(('me',))
    _name = 'skip'


class End(Pattern):
    _offset_names = set(('me', 'he', 're'))
    _name = 'end'


class Cluster(NamedSyntaxItem):

    def __init__(self, syn, name, *add_groups):
        super().__init__(syn, name)
        self.groups = set()

    @property
    def arg_name(self):
        return f'@{self.qual_name}'

    def add(self, *groups):
        for group in groups:
            if isinstance(group, str):
                self.groups.add(self.syn.group(group))
            else:
                self.groups.add(group)

    def group(self, name):
        grp = self.syn.group(name)
        self.add(grp)
        return grp

    def include(self, path_name):
        self.syn.schedule(commands.syntax, 'include', self.arg_name, path_name)
        self.syn.schedule(commands.unlet, 'b:current_syntax', bang=True)

    def invoke(self):
        if not self.groups:
            return
        names = ','.join(g.qual_name for g in self.groups)
        commands.syntax('cluster', self.qual_name, f'contains={names}')
