"""A pythonic API for creating syntax highlighting definitions."""

import functools
import weakref

import vpe
from vpe import commands


class _Singleton:
    pass


class SyntaxBase:
    _keyword_options = {}
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
    ALLBUT = _Singleton()
    ALL = _Singleton()

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
        for g in self.groups:
            assert not isinstance(g, str)

    def vim_fmt(self):
        if not self.groups:
            return ''
        if Syntax.ALL in self.groups:
            return 'contains=ALL'

        args = []
        if Syntax.ALLBUT in self.groups:
            args.append('ALLBUT')
        opt_sort = lambda x: x
        args.extend(opt_sort(
            g.arg_name for g in self.groups if g is not Syntax.ALLBUT))
        return f'{self.name}={",".join(args)}'


class GroupOption(Option):
    def __init__(self, group):
        self.group = group

    def vim_fmt(self):
        return f'{self.name}={self.group.qual_name}'


class MatchGroup(GroupOption):
    name = 'matchgroup'


class NextGroup(GroupOption):
    name = 'nextgroup'


class LocationGroup(GroupOption):
    def __init__(self, name, group):
        super().__init__(group)
        self.name = name

    def vim_fmt(self):
        return f'{self.name} {self.group.qual_name}'


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


class NoneGroup(NamedSyntaxItem):
    def __init__(self):
        pass

    @property
    def qual_name(self):
        return 'NONE'


def extract_keys(d, *names):
    extracted = {}
    for name in names:
        if name in d:
            extracted[name] = d.pop(name)
    return extracted


class Region(SyntaxBase):
    _options = {
        'concealends': lambda v: '',
        'contains': lambda v: 'f={v}',
        'display': lambda v: '',
        'extend': lambda v: '',
        'extend': lambda v: '',
        'fold': lambda v: '',
    }

    def __init__(self, syn, syn_cmd, name, **options):
        self.syn = syn
        self.syn_cmd = syn_cmd
        self.qual_name = name
        self.starts, self.skips, self.ends = [], [], []
        self.preview = options.pop('preview', False)
        self.options = convert_syntax_options(options)

    def start(self, *pat, **kwargs):
        self.starts.append(Start(*pat, **kwargs))
        return self

    def skip(self, *pat, **kwargs):
        self.skips.append(Skip(*pat, **kwargs))
        return self

    def end(self, *pat, **kwargs):
        self.ends.append(End(*pat, **kwargs))
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.syn.schedule(
                self.syn_cmd, 'region', f'{self.qual_name}',
                *[p.arg_str() for p in self.starts],
                *[p.arg_str() for p in self.skips],
                *[p.arg_str() for p in self.ends],
                *[opt.vim_fmt() for opt in self.options.values()])
            if self.preview:
                print(self.syn.preview_last())


class Group(NamedSyntaxItem):
    region_type = Region
    syn_cmd = commands.syntax
    _pre_pat_names = 'excludenl', 'keepend', 'grouphere', 'groupthere'

    def __init__(self, syn, name, std=False, contained=False):
        super().__init__(syn, name, std=std)
        self.linked = set()
        self.contained = contained

    def add_links(self, *groups):
        """Add groups to the sent that lnk to this group."""
        for group in groups:
            if isinstance(group, str):
                group = self.syn.group(group)
            self.linked.add(group)

    def add_keyword(self, *keywords, **options):
        offsets, options = self.get_offsets(options, self._match_offset_names)
        if self.contained:
            options['contained'] = True
        options = convert_syntax_options(options)
        self.syn.schedule(
            commands.syntax, 'keyword', f'{self.qual_name}', ' '.join(keywords),
            *[opt.vim_fmt() for opt in options.values()])

    def add_match(self, *pat, lidx=None, lrange=None, **options):
        """Add a syntax match for this group."""
        pats = [str(p) for p in pat]
        preview = options.pop('preview', False)
        offsets, options = self.get_offsets(options, self._match_offset_names)
        if self.contained:
            options['contained'] = True
        options = convert_syntax_options(options)
        pre_pat_options = extract_keys(options, *self._pre_pat_names)
        if lidx is not None:
            pats[0:0] =  [fr'\%{lidx + 1}l']
        elif lrange is not None:
            a, b = lrange
            prefix = ''
            if a is not None:
                prefix += fr'\%>{a}l'
            if b is not None:
                prefix += fr'\%<{b + 1}l'
            pats[0:0] =  [prefix]
        pat = ''.join(f'{p}' for p in pats)
        self.syn.schedule(
            self.syn_cmd, 'match', f'{self.qual_name}',
            *[opt.vim_fmt() for opt in pre_pat_options.values()],
            f'"{pat}"{offsets}',
            *[opt.vim_fmt() for opt in options.values()])
        if preview or self.name == 'Sync':
            print(self.syn.preview_last())

    def add_region(self, *, start=None, skip=None, end=None, **options):
        """Add a syntax region for this group.

        This is only suitable for simple region definitions. Only a single
        start, skip and end pattern can be added. For more complex cases use
        a `region` context.
        """
        with self.region_type(
                self.syn, self.syn_cmd, self.qual_name, *options) as region:
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
        if self.contained:
            options['contained'] = True
        return self.region_type(
            self.syn, self.syn_cmd, self.qual_name, **options)

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


class SyncGroup(Group):
    """A group use for synchronisation."""
    syn_cmd = functools.partial(commands.syntax, 'sync')


def convert_syntax_options(options):
    for name in options:
        if name == 'contains':
            options[name] = Contains(options[name])
        elif name == 'matchgroup':
            options[name] = MatchGroup(options[name])
        elif name == 'nextgroup':
            options[name] = NextGroup(options[name])
        elif name in ('grouphere', 'groupthere'):
            options[name] = LocationGroup(name, options[name])
        else:
            options[name] = Option(name, options[name])
    return options


class Syntax(SyntaxBase):
    """Context manager for defining syntax highlighting.

    This stores a sequence of syntax highlighting directives. The directives
    are applied when the context is exited.
    """
    group_type = Group
    sync_group_type = SyncGroup

    def __init__(self, group_prefix):
        self.prefix = group_prefix
        self._match_options['contains'] = self._expand_groups_arg
        self.groups = {}
        self.std_groups = {}
        self.clusters = {}

    def std_group(self, name):
        if name not in self.std_groups:
            self.std_groups[name] = self.group_type(self, name, std=True)
        return self.std_groups[name]

    def group(self, name, **kwargs):
        if name not in self.groups:
            self.groups[name] = self.group_type(self, name, **kwargs)
        return self.groups[name]

    def sync_group(self, name, **kwargs):
        if name not in self.groups:
            self.groups[name] = self.sync_group_type(self, name, **kwargs)
        return self.groups[name]

    def std_cluster(self, name):
        if name not in self.clusters:
            self.clusters[name] = StdCluster(self, name)
        return self.clusters[name]

    def cluster(self, name, *add_groups):
        if name not in self.clusters:
            self.clusters[name] = Cluster(self, name)
        cluster = self.clusters[name]
        cluster.add(*add_groups)
        return cluster

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


delimeter_chars = r'"/\'+?!=^_:@$%&*;~#,.'


def deliminate(p):
    used = set(p)
    for delim in delimeter_chars:
        if delim not in used:
            break
    else:
        delim = '"'
        p = p.replace('"', r'\"')
    return f'{delim}{p}{delim}'


class Pattern(SyntaxBase):

    def __init__(self, *pat, lidx=None, lrange=None, **options):
        self.pat = ''.join(str(p) for p in pat)
        self.matchgroup = options.pop('matchgroup', None)
        self.offsets, _ = self.get_offsets(options, self._offset_names)
        options = convert_syntax_options(options)
        self.pre_pat_options = extract_keys(options, *self._pre_pat_names)
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
        s = [opt.vim_fmt() for opt in self.pre_pat_options.values()]
        if self.matchgroup:
            s.append(f'matchgroup={self.matchgroup.qual_name}')
        s.append(f'{self._name}={deliminate(self.pat)}{self.offsets}')
        return ' '.join(s)


class Start(Pattern):
    _offset_names = set(('ms', 'hs', 'rs'))
    _name = 'start'
    _pre_pat_names = ('keepend', 'extend, matchgroup')


class Skip(Pattern):
    _offset_names = set(('me',))
    _name = 'skip'
    _pre_pat_names = ('keepend', 'extend')


class End(Pattern):
    _offset_names = set(('me', 'he', 're'))
    _name = 'end'
    _pre_pat_names = ('keepend', 'extend', 'excludenl', 'matchgroup')


class Cluster(NamedSyntaxItem):

    def __init__(self, syn, name):
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

    def group(self, name, **kwargs):
        grp = self.syn.group(name, **kwargs)
        self.add(grp)
        return grp

    def include(self, path_name):
        self.syn.schedule(commands.syntax, 'include', self.arg_name, path_name)

    def invoke(self):
        if not self.groups:
            return
        cont = Contains(*self.groups)
        commands.syntax('cluster', self.qual_name, cont.vim_fmt())


class StdCluster(Cluster):
    @property
    def arg_name(self):
        return f'@{self.name}'

    def invoke(self):
        return


NONE = NoneGroup()
