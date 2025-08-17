"""A pythonic API for creating syntax highlighting definitions."""
from __future__ import annotations

import functools
import weakref
from dataclasses import dataclass
from typing import (
    Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union)

from . import core, wrappers

delimeter_chars = '"\'/\\+?!=^_:@$%&*;~#,.'


@dataclass
class _Singleton:
    # pylint: disable=too-few-public-methods
    name: str


class SyntaxBase:
    """Base class for various syntax support classes."""
    # pylint: disable=too-few-public-methods
    _region_options: Dict[str, Callable] = {
        'concealends': lambda v: '',
        'contains': lambda v: 'f={v}',
        'display': lambda v: '',
        'extend': lambda v: '',
        'fold': lambda v: '',
    }
    _other_options: Dict[str, Callable] = {
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
    ALLBUT = _Singleton('ALLBUT')
    ALL = _Singleton('BUT')

    @staticmethod
    def get_offsets(
            options: dict, offset_names: Iterable[str]) -> Tuple[str, dict]:
        """Extract the offset arguments from keyword options.

        :options:      A dictionary of options.
        :offset_names: The offset option names to extract.
        :return:
            A tuple of the extracted offsets and the remaining options. The
            offsets value is a string of the form name=value[,...], ready to
            use in the Vim syntax command.
        """
        offsets = ','.join(
            f'{n}={v}' for n, v in options.items() if n in offset_names)
        options = {n: v for n, v in options.items() if n not in offset_names}
        return offsets, options


class Option:
    """Base class for the syntax command options."""
    # pylint: disable=too-few-public-methods

    def vim_fmt(self) -> str:
        """Format the option as a string for use in a :syntax command."""


class SimpleOption(Option):
    """A simple syntax option.

    :name:  The option's name.
    :value: If true then the option is enabled.
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, name: str, value: bool):
        self.name = name
        self.value = value

    def vim_fmt(self) -> str:
        """Format the option as a string for use in a :syntax command."""
        if self.value:
            return f'{self.name}'
        return ''


class Contains(Option):
    """Store for the syntax contains option.

    :groups: This can optionally be initialised with one or more groups.
    """
    # pylint: disable=too-few-public-methods
    name = 'contains'
    groups: list[Group]

    def __init__(self, *groups: "Group"):
        self.groups = []
        for g in groups:
            if isinstance(g, (tuple, list)):
                self.groups.extend(g)
            else:
                self.groups.append(g)
        for g in self.groups:
            assert not isinstance(g, str)

    def vim_fmt(self):
        if Syntax.ALL in self.groups:
            return 'contains=ALL'

        args = []
        if Syntax.ALLBUT in self.groups:
            args.append('ALLBUT')
        args.extend(
            g.arg_name for g in sorted(self.groups, key=lambda g: g.name)
            if g is not Syntax.ALLBUT)
        return f'{self.name}={",".join(args)}'


class GroupOption(Option):
    """Base class for group options.

    :group: A group instance.
    """
    # pylint: disable=too-few-public-methods
    name: str = ''

    def __init__(self, group: "Group"):
        self.group = group

    def vim_fmt(self):
        return f'{self.name}={self.group.qual_name}'


class MatchGroup(GroupOption):
    """A matchgroup option."""
    # pylint: disable=too-few-public-methods
    name = 'matchgroup'


class ContainedIn(GroupOption):
    """A containedin option."""
    # pylint: disable=too-few-public-methods
    name = 'containedin'


class NextGroup(GroupOption):
    """A nextgroup option."""
    # pylint: disable=too-few-public-methods
    name = 'nextgroup'


class LocationGroup(GroupOption):
    """A grouphere or groupthere option.

    :name:  The option name - 'grouphere' or groupthere'.
    :group: A group instance.
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, name, group):
        super().__init__(group)
        self.name = name

    def vim_fmt(self):
        return f'{self.name} {self.group.qual_name}'


class NamedSyntaxItem(SyntaxBase):
    """A syntax item with an assigned name.

    :syn:  The `Syntax` instance that created this item.
    :name: A name for the item.
    :std:  If true then the item is treated as not in the Syntax object's
           namespace.
    """
    def __init__(self, syn: "Syntax", name: str, std=False):
        self.syn = weakref.proxy(syn)
        self._name = name
        self._std = std

    @property
    def name(self) -> str:
        """The base name of this item, without the Sytntax ojbect's prefix."""
        return self._name

    @property
    def qual_name(self) -> str:
        """The qualified name of this item.

        It this was created with std=True then this is the same as the `name`.
        Otherwise the parent Syntax object's namespace is assed to `name` as a
        prefix.
        """
        if self._std:
            return self._name
        return self.syn.fmt_group(self._name)

    @property
    def arg_name(self) -> str:
        """A suitable name when used as an argument."""
        return self.qual_name


class _NoneGroup(NamedSyntaxItem):
    def __init__(self):
        # pylint: disable=super-init-not-called
        pass

    @property
    def qual_name(self):
        """The qualified name of this item - fixed as NONE."""
        return 'NONE'


class Region(SyntaxBase):
    """A context manager for adding a region  to a group.

    :syn:     The `Syntax` instance that created this item.
    :syn_cmd: The syntax command function.
    :name:    A name for the item.
    :options: Named options for the region command.
    """
    # pylint: disable=too-many-instance-attributes
    _options = {
        'concealends': lambda v: '',
        'contains': lambda v: 'f={v}',
        'display': lambda v: '',
        'extend': lambda v: '',
        'fold': lambda v: '',
    }

    def __init__(self, syn: "Syntax", syn_cmd: Callable, name: str, **options):
        self.syn = syn
        self.syn_cmd = syn_cmd
        self.qual_name = name
        self.directives: list[Start | Skip | End | MatchGroupDirective] = []
        self.preview = options.pop('preview', False)
        self.options = convert_syntax_options(self.syn, options)

    def matchgroup(self, group: Group | None):
        """Add or remove a matchgroup directive for this region."""
        self.directives.append(MatchGroupDirective(group))

    def start(self, pat: str, *pats: str, **kwargs) -> "Region":
        """Define a start pattern

        :pat:    The first part of the regular expression string.
        :pats:   Additional expression strings. These are concatenated with
                 *pat* to form the complete regular expression.
        :kwargs: Additional options for the region start.
        """
        self.directives.append(Start(pat, *pats, **kwargs))
        return self

    def skip(self, pat: str, *pats: str, **kwargs) -> "Region":
        """Define a skip pattern

        :pat:    The first part of the regular expression string.
        :pats:   Additional expression strings. These are concatenated with
                 *pat* to form the complete regular expression.
        :kwargs: Additional options for the region skip.
        """
        self.directives.append(Skip(pat, *pats, **kwargs))
        return self

    def end(self, pat: str, *pats: str, **kwargs) -> "Region":
        """Define an end pattern

        :pat:    The first part of the regular expression string.
        :pats:   Additional expression strings. These are concatenated with
                 *pat* to form the complete regular expression.
        :kwargs: Additional options for the region skip.
        """
        self.directives.append(End(pat, *pats, **kwargs))
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.syn.schedule(
                self.syn_cmd, 'region', f'{self.qual_name}',
                *[p.arg_str() for p in self.directives],
                *[opt.vim_fmt() for opt in self.options.values()])
            if self.preview:                                 # pragma: no cover
                core.log(self.syn.preview_last())


class Group(NamedSyntaxItem):
    """A named syntax group.

    :syn:       The `Syntax` instance that created this item.
    :name:      A name for the item.
    :std:       If true then the group is treated as not in the Syntax object's
                namespace.
    :contained: If true then all matches, keywords and regions this creates
                automatically have the contained option set.
    """
    region_type = Region
    _pre_pat_names = 'excludenl', 'keepend', 'grouphere', 'groupthere'

    def __init__(self, syn, name, std=False, contained=False):
        super().__init__(syn, name, std=std)
        self.linked = set()
        self.contained = contained
        self.hl_args = {}
        self.syn_cmd = wrappers.commands.syntax

    def add_links(self, *groups):
        """Add groups to the set that link to this group."""
        for group in groups:
            if isinstance(group, str):
                self.linked.add(self.syn.group(group))
            else:
                self.linked.add(group)

    def add_keyword(self, keyword, *keywords, **options):
        """Add one or more keywords to this syntax group.

        :keyword:  The first keyword to add.
        :keywords: Additional keywords to add.
        :options:  Options for the set of keywords.
        """
        keywords = keyword, *keywords
        _, options = self.get_offsets(options, self._match_offset_names)
        if self.contained and 'contained' not in options:
            options['contained'] = True
        options = convert_syntax_options(self.syn, options)
        self.syn.schedule(
            wrappers.commands.syntax, 'keyword', f'{self.qual_name}',
            ' '.join(keywords),
            *[opt.vim_fmt() for opt in options.values() if opt.vim_fmt()])

    def add_match(
            self, pat: str, *pats: str, lidx: Optional[int] = None,
            lrange: Optional[Tuple[int, int]] = None, **options):
        """Add a syntax match for this group.

        :pat:     The first part of the regular expression string.
        :pats:    Additional expression strings. These are concatenated with
                  *pat* to form the complete regular expression.
        :lidx:    The index of a line to tie the match to.
        :lrange:  A range of lines to tie the match to.
        :options: Additional options for the match.
        """
        all_pats = [str(p) for p in (pat, *pats)]
        preview = options.pop('preview', False)
        offsets, options = self.get_offsets(options, self._match_offset_names)
        if self.contained and 'contained' not in options:
            options['contained'] = True
        options = convert_syntax_options(self.syn, options)
        pre_pat_options = extract_keys(options, *self._pre_pat_names)
        if lidx is not None:
            all_pats[0:0] = [fr'\%{lidx + 1}l']
        elif lrange is not None:
            a, b = lrange
            prefix = ''
            if a is not None:
                prefix += fr'\%>{a}l'
            if b is not None:
                prefix += fr'\%<{b + 1}l'
            all_pats[0:0] = [prefix]
        pat = ''.join(f'{p}' for p in all_pats)
        self.syn.schedule(
            self.syn_cmd, 'match', f'{self.qual_name}',
            *[opt.vim_fmt() for opt in pre_pat_options.values()],
            f'{deliminate(pat)}{offsets}',
            *[opt.vim_fmt() for opt in options.values()])
        if preview:                                          # pragma: no cover
            core.log(self.syn.preview_last())

    def add_region(
            self, *, start: str, end: str, skip: Optional[str] = None,
            **options):
        """Add a syntax region for this group.

        This is only suitable for simple region definitions. Only a single
        start, skip and end pattern can be added. For more complex cases use
        a `region` context.

        :start:   The start pattern.
        :end:     The end pattern.
        :skip:    Optional skip pattern.
        :options: Additional options for the region.
        """
        if self.contained and 'contained' not in options:
            options['contained'] = True
        with self.region_type(
                self.syn, self.syn_cmd, self.qual_name, **options) as region:
            region.start(start)
            if skip:
                region.skip(skip)
            region.end(end)

    def region(self, **options):
        """Create a region context manager.

        This supports regions with multiple start, skip and end patterns.

        :options: Additional options for the region.
        """
        if self.contained and 'contained' not in options:
            options['contained'] = True
        return self.region_type(
            self.syn, self.syn_cmd, self.qual_name, **options)

    def highlight(self, **kwargs):
        """Define highlighting for this group.

        :kwargs:
            These are the same as for `vpe.highlight`, except that ``group``
            and ``clear`` should not be  used.
        """
        self.hl_args.update(kwargs)

    def set_highlight(self, file=None):
        """Set up highlight definition for this group."""
        if self.hl_args:
            core.highlight(group=self.qual_name, **self.hl_args, file=file)

    def invoke(self, file=None) -> None:
        """Invoke any pending syntax commands.

        This is only intended to be used by a `Syntax` instance.
        """
        hilink = functools.partial(
            wrappers.commands.highlight, 'default', 'link', bang=True,
            file=file)
        for group in sorted(self.linked, key=lambda g: g.qual_name):
            hilink(group.qual_name, self.qual_name)


class SyncGroup(Group):
    """A group use for synchronisation."""
    def __init__(self, syn, name, std=False, contained=False):
        super().__init__(syn, name, std=std, contained=contained)
        self.syn_cmd = functools.partial(wrappers.commands.syntax, 'sync')


class Syntax(SyntaxBase):
    """Context manager for defining syntax highlighting.

    This stores a sequence of syntax highlighting directives. The directives
    are executed (as syntax and highlight commands) when the context is exited.

    :group_prefix: A prefix added to the name of all groups created using this
                   Syntax instance.
    :clear:        Whether to clear any previous syntax for the current buffer.
                   This is ``True`` by default.
    """
    group_type = Group
    sync_group_type = SyncGroup
    _directives: List[Tuple[Callable, Tuple, Dict]]

    def __init__(self, group_prefix, clear: bool = True):
        self.prefix = group_prefix
        self.groups: Dict[str, Group] = {}
        self.std_groups: Dict[str, Group] = {}
        self.clusters: Dict[str, Cluster] = {}
        self.simple_includes: List[str] = []
        self.clear_prev_syntax = clear
        self.spell = self.std_group('@Spell')
        self.no_spell = self.std_group('@NoSpell')

    def std_group(self, name):
        """Create a standard (externally defined) group.

        :name: The group's full name.
        """
        if name not in self.std_groups:
            self.std_groups[name] = self.group_type(self, name, std=True)
        return self.std_groups[name]

    def group(self, name, link_to=None, **options):
        """Create a group within this `syntax` object's namespace.

        :name:    The group's name.
        :link_to: The full name of a group to link to.
        :options: Options for the group.
        """
        if name not in self.groups:
            self.groups[name] = self.group_type(self, name, **options)
        group = self.groups[name]
        if link_to is not None:
            self.std_group(link_to).add_links(group)
        return group

    def sync_group(self, name, **options):
        """Create a sync group within this `syntax` object's namespace.

        :name:    The group's name.
        :options: Options for the group.
        """
        if name not in self.groups:
            self.groups[name] = self.sync_group_type(self, name, **options)
        return self.groups[name]

    def std_cluster(self, name):
        """Create a standard (externally defined) cluster.

        :name: The cluster's full name.
        """
        if name not in self.clusters:
            self.clusters[name] = StdCluster(self, name)
        return self.clusters[name]

    def cluster(self, name, *add_groups):
        """Create a cluster within this `syntax` object's namespace.

        :name: The cluster's name.
        """
        if name not in self.clusters:
            self.clusters[name] = Cluster(self, name)
        cluster = self.clusters[name]
        if add_groups:
            cluster.add(*add_groups)
        return cluster

    def include(self, name):
        """Do a simple include of syntax file.

        The command executed is: runtime syntax/name.vim

        :name: The syntax name.
        """
        self.simple_includes.append(name)

    def fmt_group(self, name: str) -> str:
        """Format the name of a group, adding the Syntax object's prefix.

        :name: The name of the group.
        """
        return f'{self.prefix}{name}'

    def schedule(self, func, *args, **kwargs):
        """Add a syntax command to those scheduled for later execution.

        :func:   The syntax command function.
        :args:   Positional arguments for the command.
        :kwargs: Keyword arguments for the command.
        """
        self._directives.append((func, args, kwargs))

    def preview_last(self) -> str:
        """Generate preview string of the last scheduled command.

        This can be useful during debugging a new syntax.
        """
        func, args, kwargs = self._directives[-1]
        return func(*args, **kwargs, preview=True)

    def __enter__(self):
        self._directives = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.clear_prev_syntax:
            wrappers.commands.syntax('clear')
        for syn_name in self.simple_includes:
            wrappers.commands.runtime(f'syntax/{syn_name}.vim')
        for func, args, kwargs in self._directives:
            func(*args, **kwargs)
        for cluster in self.clusters.values():
            cluster.invoke()
        for group in self.groups.values():
            group.invoke()
        for group in self.std_groups.values():
            group.invoke()
        for group in self.groups.values():
            group.set_highlight()


class Pattern(SyntaxBase):
    """A syntax pattern.

    :pat:     The first part of the regular expression string.
    :pats:    Additional expression strings. These are concatenated with *pat*
              to form the complete regular expression.
    :lidx:    The index of a line to tie the match to.
    :lrange:  A range of lines to tie the match to.
    :options: Additional options, including pattern offsets.
    """
    _offset_names: Set
    _name: str
    _pre_pat_names: Tuple[str, ...]

    def __init__(self, pat, *pats, lidx=None, lrange=None, **options):
        pats = pat, *pats
        self.pat = ''.join(str(p) for p in pats)
        self.matchgroup = options.pop('matchgroup', None)
        self.offsets, _ = self.get_offsets(options, self._offset_names)
        options = convert_syntax_options(None, options)
        self.pre_pat_options = extract_keys(options, *self._pre_pat_names)
        if lidx is not None:
            self.pat = fr'\%{lidx + 1}l' + self.pat
        elif lrange is not None:
            a, b = lrange
            prefix = ''
            if a is not None:
                prefix += fr'\%>{a}l'
            if b is not None:
                prefix += fr'\%<{b + 1}l'
            self.pat = prefix + self.pat

    def arg_str(self) -> str:
        """Format pattern as an argument to a syntax command."""
        s = [opt.vim_fmt() for opt in self.pre_pat_options.values()]
        if self.matchgroup:
            s.append(f'matchgroup={self.matchgroup.qual_name}')
        s.append(f'{self._name}={deliminate(self.pat)}{self.offsets}')
        return ' '.join(s)


class Start(Pattern):
    """A start pattern."""
    _offset_names = set(('ms', 'hs', 'rs'))
    _name = 'start'
    _pre_pat_names = ('keepend', 'extend, matchgroup')


class Skip(Pattern):
    """A skip pattern."""
    _offset_names = set(('me',))
    _name = 'skip'
    _pre_pat_names = ('keepend', 'extend')


class End(Pattern):
    """An end pattern."""
    _offset_names = set(('me', 'he', 're'))
    _name = 'end'
    _pre_pat_names = ('keepend', 'extend', 'excludenl', 'matchgroup')


class MatchGroupDirective:
    """A matchgroup directive for a region."""
    def __init__(self, group: Group | None):
        self.group = group

    def arg_str(self) -> str:
        """Format matchgroup as an directove in a region command."""
        name = self.group.qual_name if self.group else 'NONE'
        return f'matchgroup={name}'


class Cluster(NamedSyntaxItem):
    """ A cluster of groups.

    :syn:  The `Syntax` instance that created this cluster.
    :name: A name for this cluster.
    """
    def __init__(self, syn, name):
        super().__init__(syn, name)
        self.groups: list[Group] = []

    @property
    def arg_name(self):
        return f'@{self.qual_name}'

    def add(self, group1: Union[Group, str], *groups: Union[Group, str]):
        """Add groups to the cluster.

        A group argument may be a name, in which case it references or creates
        a group within the parent `syntax` object.

        :group1: The first group to be added.
        :groups: Additional groups to be added.
        """
        for group in (group1, *groups):
            g = self.syn.group(group) if isinstance(group, str) else group
            if g not in self.groups:
                self.groups.append(g)

    def group(self, name, **options):
        """Create and add a new group.

        The new group is within the parent `Syntax` objects namespace. This
        provides a convenient shortcut for:<py>:

            g = syntax.group(name, ...)
            cluster.add(g)

        :name:    The name of the group.
        :options: Options for the group.
        """
        grp = self.syn.group(name, **options)
        self.add(grp)
        return grp

    def include(self, path_name):
        """Include Vim syntax file, adding its groups to this cluster.

        This does a :vim:`syn-include` operation with a cluster name.

        :path_name: The path name of the syntax file to include. If this is
                    a relative path, the file is searched for within the
                    ::vim:`runtimepath`.
        """
        self.syn.schedule(
            wrappers.commands.syntax, 'include', self.arg_name, path_name)

    def invoke(self, file=None) -> None:
        """Invoke any pending syntax commands.

        This is only intended to be used by a `Syntax` instance.
        """
        if not self.groups:
            return
        cont = Contains(*self.groups)
        wrappers.commands.syntax(
            'cluster', self.qual_name, cont.vim_fmt(), file=file)


class StdCluster(Cluster):
    """A cluster of groups, not in a `Syntax` object's namespace."""
    @property
    def arg_name(self):
        """A suitable name when used as an argument."""
        return f'@{self.name}'

    def invoke(self) -> None:
        """Null operation implementation."""


def deliminate(pat: str) -> str:
    """Put deliminators around a syntax expression.

    If reasonably sensible, a deliminator that is not part of the pattern is
    used. If this is not possible then the double quote character is used and
    any double quotes within the pattern are escaped with a backslash.

    :pat: The pattern to be deliminated.
    """
    used = set(pat)
    for delim in delimeter_chars:
        if delim not in used:
            break
    else:
        delim = '"'
        pat = pat.replace('"', r'\"')
    return f'{delim}{pat}{delim}'


def convert_syntax_options(syn, options) -> dict:
    """Convert values in a dictionary of option to `Option` instances.

    :options: The dictionary containing keyword defined options.
    :return:  The same (modified in place) dictionary.
    """
    sp = None
    spell = options.pop('spell', None)
    if spell is not None and syn is not None:
        if spell:
            sp = syn.spell
        else:
            sp = syn.no_spell

    for name in list(options):
        if name == 'contains':
            if options[name]:
                options[name] = Contains(options[name])
                if sp:
                    options[name].groups.append(sp)
            else:
                if sp:
                    options[name] = Contains(sp)
                else:
                    del options[name]
        elif name == 'matchgroup':
            options[name] = MatchGroup(options[name])
        elif name == 'containedin':
            options[name] = ContainedIn(options[name])
        elif name == 'nextgroup':
            options[name] = NextGroup(options[name])
        elif name in ('grouphere', 'groupthere'):
            options[name] = LocationGroup(name, options[name])
        else:
            options[name] = SimpleOption(name, options[name])

    if 'contains' not in options and sp:
        options['spell'] = Contains(sp)
    return options


def extract_keys(source_dict: dict, *keys: Any) -> dict:
    """Extract a set of named items from a dictionary.

    Any item in *source_dict* that has a key contained in *keys* is moved to
    a new dictionary.

    :source_dict: The dictionary from which to extract the items.
    :keys:        The keys for the items to extract.
    :return:
        A new dictionary containing the items remove from the *source_dict*.
    """
    extracted = {}
    for name in keys:
        if name in source_dict:
            extracted[name] = source_dict.pop(name)
    return extracted


NONE = _NoneGroup()
