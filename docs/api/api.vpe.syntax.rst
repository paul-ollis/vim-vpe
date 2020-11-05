Module vpe.syntax
=================

.. py:module:: vpe.syntax

A pythonic API for creating syntax highlighting definitions.

Cluster
-------

.. py:class:: vpe.syntax.Cluster(syn,name)

    A cluster of groups.


    **Parameters**

    .. container:: parameters itemdetails

        *syn*
            The `Syntax` instance that created this cluster.
        *name*
            A name for this cluster.

    **Methods**

        .. py:method:: vpe.syntax.Cluster.add(...)

            .. parsed-literal::

                add(
                    group1: Union[vpe.syntax.Group, str],
                    \*groups: Union[vpe.syntax.Group, str])

            Add groups to the cluster.

            A group argument may be a name, in which case it references or creates
            a group within the parent `syntax` object.

            **Parameters**

            .. container:: parameters itemdetails

                *group1*: typing.Union[vpe.syntax.Group, str]
                    The first group to be added.
                *groups*: typing.Union[vpe.syntax.Group, str]
                    Additional groups to be added.

        .. py:method:: vpe.syntax.Cluster.group(name,**options)

            Create and add a new group.

            The new group is within the parent `Syntax` objects namespace. This
            provides a convenient shortcut for:

            .. code-block:: py

                g = syntax.group(name, ...)
                cluster.add(g)

            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The name of the group.
                *options*
                    Options for the group.

        .. py:method:: vpe.syntax.Cluster.include(path_name)

            Include Vim syntax file, adding its groups to this cluster.

            This does a :vim:`syn-include` operation with a a cluster name.

            **Parameters**

            .. container:: parameters itemdetails

                *path_name*
                    The path name of the syntax file to include. If this is
                    a relative path, the file is searched for within the
                    ::vim:`runtimepath`.

        .. py:method:: vpe.syntax.Cluster.invoke() -> None

            Invoke any pending syntax commands.

            This is only intended to be used by a `Syntax` instance.

Contains
--------

.. py:class:: vpe.syntax.Contains(*groups: Group)

    Store for the syntax contains option.


    **Parameters**

    .. container:: parameters itemdetails

        *groups*: typing.List[vpe.syntax.Group]
            This can optionally be initialised with one or more groups.

End
---

.. py:class:: vpe.syntax.End(pat,*pats,lidx=None,lrange=None,**options)

    An end pattern.

Group
-----

.. py:class:: vpe.syntax.Group(syn,name,std=False,contained=False)

    A named syntax group.


    **Parameters**

    .. container:: parameters itemdetails

        *syn*
            The `Syntax` instance that created this item.
        *name*
            A name for the item.
        *std*
            If true then the group is treated as not in the Syntax object's
            namespace.
        *contained*
            If true then all matches, keywords and regions this creates
            automtically have the contained option set.

    .. py:class:: vpe.syntax.Group.region_type(syn: Syntax,syn_cmd: typing.Callable,name: str,**options)

        A context manager for adding a region  to a group.


        **Parameters**

        .. container:: parameters itemdetails

            *syn*
                The `Syntax` instance that created this item.
            *syn_cmd*
                The syntax command function.
            *name*
                A name for the item.
            *options*
                Named options for the region command.

        **Methods**

            .. py:method:: vpe.syntax.Group.region_type.end(pat: str,*pats: str,**kwargs) -> Region

                Define an end pattern


                **Parameters**

                .. container:: parameters itemdetails

                    *pat*: str
                        The first part of the regular expression string.
                    *pats*: str
                        Additional expression strings. These are concatenated with
                        *pat* to form the complete regular expression.
                    *kwargs*
                        Additional options for the region skip.

            .. py:method:: vpe.syntax.Group.region_type.skip(pat: str,*pats: str,**kwargs) -> Region

                Define a skip pattern


                **Parameters**

                .. container:: parameters itemdetails

                    *pat*: str
                        The first part of the regular expression string.
                    *pats*: str
                        Additional expression strings. These are concatenated with
                        *pat* to form the complete regular expression.
                    *kwargs*
                        Additional options for the region skip.

            .. py:method:: vpe.syntax.Group.region_type.start(pat: str,*pats: str,**kwargs) -> Region

                Define a start pattern


                **Parameters**

                .. container:: parameters itemdetails

                    *pat*: str
                        The first part of the regular expression string.
                    *pats*: str
                        Additional expression strings. These are concatenated with
                        *pat* to form the complete regular expression.
                    *kwargs*
                        Additional options for the region start.

    **Methods**

        .. py:method:: vpe.syntax.Group.add_keyword(keyword,*keywords,**options)

            Add one or more keywords to this syntax group.


            **Parameters**

            .. container:: parameters itemdetails

                *keyword*
                    The first tkeyword to add.
                *keywords*
                    Additional tkeywords to add.
                *options*
                    Options for the set of keywords.

        .. py:method:: vpe.syntax.Group.add_links(*groups)

            Add groups to the set that link to this group.

        .. py:method:: vpe.syntax.Group.add_match(...)

            .. parsed-literal::

                add_match(
                    pat: str,
                    \*pats: str,
                    \*,
                    lidx: Optional[int] = None,
                    lrange: Optional[Tuple[int, int]] = None,
                    \*\*options)

            Add a syntax match for this group.


            **Parameters**

            .. container:: parameters itemdetails

                *pat*: str
                    The first part of the regular expression string.
                *pats*: str
                    Additional expression strings. These are concatenated with
                    *pat* to form the complete regular expression.
                *lidx*: typing.Optional[int]
                    The index of a line to tie the match to.
                *lrange*: typing.Optional[typing.Tuple[int, int]]
                    A range of lines to tie the match to.
                *options*
                    Additional options for the match.

        .. py:method:: vpe.syntax.Group.add_region(start: str,end: str,skip: Optional[str] = None,**options)

            Add a syntax region for this group.

            This is only suitable for simple region definitions. Only a single
            start, skip and end pattern can be added. For more complex cases use
            a `region` context.

            **Parameters**

            .. container:: parameters itemdetails

                *start*: str
                    The start pattern.
                *end*: str
                    The end pattern.
                *skip*: typing.Optional[str]
                    Optional skip pattern.
                *options*
                    Additional options for the region.

        .. py:method:: vpe.syntax.Group.highlight(**kwargs)

            Define highlighting for this group.


            **Parameters**

            .. container:: parameters itemdetails

                *kwargs*
                    These are the same as for `vpe.highlight`, except that ``group``
                    and ``clear`` should not be  used.

        .. py:method:: vpe.syntax.Group.invoke() -> None

            Invoke any pending syntax commands.

            This is only intended to be used by a `Syntax` instance.

        .. py:method:: vpe.syntax.Group.region(**options)

            Create a region context manager.

            This supports regions with multiple start, skip and end patterns.

            **Parameters**

            .. container:: parameters itemdetails

                *options*
                    Additional options for the region.

        .. py:method:: vpe.syntax.Group.set_highlight()

            Set up highlight definition for this group.

GroupOption
-----------

.. py:class:: vpe.syntax.GroupOption(group: Group)

    Base class for group options.


    **Parameters**

    .. container:: parameters itemdetails

        *group*
            A group instance.

LocationGroup
-------------

.. py:class:: vpe.syntax.LocationGroup(name,group)

    A grouphere or groupthere option.


    **Parameters**

    .. container:: parameters itemdetails

        *name*: str
            The option name - 'grouphere' or groupthere'.
        *group*
            A group instance.

MatchGroup
----------

.. py:class:: vpe.syntax.MatchGroup(group: Group)

    A matchgroup option.

NamedSyntaxItem
---------------

.. py:class:: vpe.syntax.NamedSyntaxItem(syn: Syntax,name: str,std=False)

    A syntax item with an assigned name.


    **Parameters**

    .. container:: parameters itemdetails

        *syn*
            The `Syntax` instance that created this item.
        *name*
            A name for the item.
        *std*
            If true then the item is treated as not in the Syntax object's
            namespace.

    **Properties**

        .. py:method:: vpe.syntax.NamedSyntaxItem.arg_name() -> str
            :property:

            A suitable name when used as an argument.

        .. py:method:: vpe.syntax.NamedSyntaxItem.name() -> str
            :property:

            The base name of this item, without the Sytntax ojbect's prefix.

        .. py:method:: vpe.syntax.NamedSyntaxItem.qual_name() -> str
            :property:

            The qualified name of this item.

            It this was created with std=True then this is the same as the `name`.
            Otherwise the parent Syntax object's namespace is assed to `name` as a
            prefix.

NextGroup
---------

.. py:class:: vpe.syntax.NextGroup(group: Group)

    A nextgroup option.

Option
------

.. py:class:: vpe.syntax.Option

    Base class for the syntax command options.

    **Methods**

        .. py:method:: vpe.syntax.Option.vim_fmt() -> str

            Format the option as a string for use in a :syntax command.

Pattern
-------

.. py:class:: vpe.syntax.Pattern(pat,*pats,lidx=None,lrange=None,**options)

    A syntax pattern.


    **Parameters**

    .. container:: parameters itemdetails

        *pat*
            The first part of the regular expression string.
        *pats*
            Additional expression strings. These are concatenated with *pat*
            to form the complete regular expression.
        *lidx*
            The index of a line to tie the match to.
        *lrange*
            A range of lines to tie the match to.
        *options*
            Additional options, including pattern offsets.

    **Methods**

        .. py:method:: vpe.syntax.Pattern.arg_str() -> str

            Format pattern as an argument to a ayntax command.

Region
------

.. py:class:: vpe.syntax.Region(syn: Syntax,syn_cmd: typing.Callable,name: str,**options)

    A context manager for adding a region  to a group.


    **Parameters**

    .. container:: parameters itemdetails

        *syn*
            The `Syntax` instance that created this item.
        *syn_cmd*
            The syntax command function.
        *name*
            A name for the item.
        *options*
            Named options for the region command.

    **Methods**

        .. py:method:: vpe.syntax.Region.end(pat: str,*pats: str,**kwargs) -> Region

            Define an end pattern


            **Parameters**

            .. container:: parameters itemdetails

                *pat*: str
                    The first part of the regular expression string.
                *pats*: str
                    Additional expression strings. These are concatenated with
                    *pat* to form the complete regular expression.
                *kwargs*
                    Additional options for the region skip.

        .. py:method:: vpe.syntax.Region.skip(pat: str,*pats: str,**kwargs) -> Region

            Define a skip pattern


            **Parameters**

            .. container:: parameters itemdetails

                *pat*: str
                    The first part of the regular expression string.
                *pats*: str
                    Additional expression strings. These are concatenated with
                    *pat* to form the complete regular expression.
                *kwargs*
                    Additional options for the region skip.

        .. py:method:: vpe.syntax.Region.start(pat: str,*pats: str,**kwargs) -> Region

            Define a start pattern


            **Parameters**

            .. container:: parameters itemdetails

                *pat*: str
                    The first part of the regular expression string.
                *pats*: str
                    Additional expression strings. These are concatenated with
                    *pat* to form the complete regular expression.
                *kwargs*
                    Additional options for the region start.

SimpleOption
------------

.. py:class:: vpe.syntax.SimpleOption(name: str,value: bool)

    A simple syntax option.


    **Parameters**

    .. container:: parameters itemdetails

        *name*
            The option's name.
        *value*
            If true then the option is enabled.

    **Methods**

        .. py:method:: vpe.syntax.SimpleOption.vim_fmt() -> str

            Format the option as a string for use in a :syntax command.

Skip
----

.. py:class:: vpe.syntax.Skip(pat,*pats,lidx=None,lrange=None,**options)

    A skip pattern.

Start
-----

.. py:class:: vpe.syntax.Start(pat,*pats,lidx=None,lrange=None,**options)

    A start pattern.

StdCluster
----------

.. py:class:: vpe.syntax.StdCluster(syn,name)

    A cluster of groups, not in a `Syntax` object's namespace.

    **Properties**

        .. py:method:: vpe.syntax.StdCluster.arg_name()
            :property:

            A suitable name when used as an argument.

    **Methods**

        .. py:method:: vpe.syntax.StdCluster.invoke() -> None

            Null operation implementation.

SyncGroup
---------

.. py:class:: vpe.syntax.SyncGroup(syn,name,std=False,contained=False)

    A group use for synchronisation.

Syntax
------

.. py:class:: vpe.syntax.Syntax(group_prefix)

    Context manager for defining syntax highlighting.

    This stores a sequence of syntax highlighting directives. The directives
    are executed (as syntax and highlight commands) when the context is exited.

    .. py:class:: vpe.syntax.Syntax.group_type(syn,name,std=False,contained=False)

        A named syntax group.


        **Parameters**

        .. container:: parameters itemdetails

            *syn*
                The `Syntax` instance that created this item.
            *name*
                A name for the item.
            *std*
                If true then the group is treated as not in the Syntax object's
                namespace.
            *contained*
                If true then all matches, keywords and regions this creates
                automtically have the contained option set.

        .. py:class:: vpe.syntax.Syntax.group_type.region_type(syn: Syntax,syn_cmd: typing.Callable,name: str,**options)

            A context manager for adding a region  to a group.


            **Parameters**

            .. container:: parameters itemdetails

                *syn*
                    The `Syntax` instance that created this item.
                *syn_cmd*
                    The syntax command function.
                *name*
                    A name for the item.
                *options*
                    Named options for the region command.

            **Methods**

                .. py:method:: vpe.syntax.Syntax.group_type.region_type.end(pat: str,*pats: str,**kwargs) -> Region

                    Define an end pattern


                    **Parameters**

                    .. container:: parameters itemdetails

                        *pat*: str
                            The first part of the regular expression string.
                        *pats*: str
                            Additional expression strings. These are concatenated with
                            *pat* to form the complete regular expression.
                        *kwargs*
                            Additional options for the region skip.

                .. py:method:: vpe.syntax.Syntax.group_type.region_type.skip(pat: str,*pats: str,**kwargs) -> Region

                    Define a skip pattern


                    **Parameters**

                    .. container:: parameters itemdetails

                        *pat*: str
                            The first part of the regular expression string.
                        *pats*: str
                            Additional expression strings. These are concatenated with
                            *pat* to form the complete regular expression.
                        *kwargs*
                            Additional options for the region skip.

                .. py:method:: vpe.syntax.Syntax.group_type.region_type.start(pat: str,*pats: str,**kwargs) -> Region

                    Define a start pattern


                    **Parameters**

                    .. container:: parameters itemdetails

                        *pat*: str
                            The first part of the regular expression string.
                        *pats*: str
                            Additional expression strings. These are concatenated with
                            *pat* to form the complete regular expression.
                        *kwargs*
                            Additional options for the region start.

        **Methods**

            .. py:method:: vpe.syntax.Syntax.group_type.add_keyword(keyword,*keywords,**options)

                Add one or more keywords to this syntax group.


                **Parameters**

                .. container:: parameters itemdetails

                    *keyword*
                        The first tkeyword to add.
                    *keywords*
                        Additional tkeywords to add.
                    *options*
                        Options for the set of keywords.

            .. py:method:: vpe.syntax.Syntax.group_type.add_links(*groups)

                Add groups to the set that link to this group.

            .. py:method:: vpe.syntax.Syntax.group_type.add_match(...)

                .. parsed-literal::

                    add_match(
                        pat: str,
                        \*pats: str,
                        \*,
                        lidx: Optional[int] = None,
                        lrange: Optional[Tuple[int, int]] = None,
                        \*\*options)

                Add a syntax match for this group.


                **Parameters**

                .. container:: parameters itemdetails

                    *pat*: str
                        The first part of the regular expression string.
                    *pats*: str
                        Additional expression strings. These are concatenated with
                        *pat* to form the complete regular expression.
                    *lidx*: typing.Optional[int]
                        The index of a line to tie the match to.
                    *lrange*: typing.Optional[typing.Tuple[int, int]]
                        A range of lines to tie the match to.
                    *options*
                        Additional options for the match.

            .. py:method:: vpe.syntax.Syntax.group_type.add_region(start: str,end: str,skip: Optional[str] = None,**options)

                Add a syntax region for this group.

                This is only suitable for simple region definitions. Only a single
                start, skip and end pattern can be added. For more complex cases use
                a `region` context.

                **Parameters**

                .. container:: parameters itemdetails

                    *start*: str
                        The start pattern.
                    *end*: str
                        The end pattern.
                    *skip*: typing.Optional[str]
                        Optional skip pattern.
                    *options*
                        Additional options for the region.

            .. py:method:: vpe.syntax.Syntax.group_type.highlight(**kwargs)

                Define highlighting for this group.


                **Parameters**

                .. container:: parameters itemdetails

                    *kwargs*
                        These are the same as for `vpe.highlight`, except that ``group``
                        and ``clear`` should not be  used.

            .. py:method:: vpe.syntax.Syntax.group_type.invoke() -> None

                Invoke any pending syntax commands.

                This is only intended to be used by a `Syntax` instance.

            .. py:method:: vpe.syntax.Syntax.group_type.region(**options)

                Create a region context manager.

                This supports regions with multiple start, skip and end patterns.

                **Parameters**

                .. container:: parameters itemdetails

                    *options*
                        Additional options for the region.

            .. py:method:: vpe.syntax.Syntax.group_type.set_highlight()

                Set up highlight definition for this group.

    .. py:class:: vpe.syntax.Syntax.sync_group_type(syn,name,std=False,contained=False)

        A group use for synchronisation.

    **Methods**

        .. py:method:: vpe.syntax.Syntax.cluster(name,*add_groups)

            Create a cluster within this `syntax` object's namespace.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The cluster's name.

        .. py:method:: vpe.syntax.Syntax.fmt_group(name: str) -> str

            Format the name of a group, adding the Syntax object's prefix.


            **Parameters**

            .. container:: parameters itemdetails

                *name*: str
                    The name of the group.

        .. py:method:: vpe.syntax.Syntax.group(name,link_to=None,**options)

            Create a group within this `syntax` object's namespace.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The group's name.
                *link_to*
                    The full name of a group to link to.
                *options*
                    Options for the group.

        .. py:method:: vpe.syntax.Syntax.include(name)

            Do a simple include of syntax file.

            The command executed is: runtime syntax/name.vim

            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The syntax name.

        .. py:method:: vpe.syntax.Syntax.preview_last() -> str

            Generate preview string of the last scheduled command.

            This can be useful during debugging a new syntax.

        .. py:method:: vpe.syntax.Syntax.schedule(func,*args,**kwargs)

            Add a syntax command to those scheduled for later execution.


            **Parameters**

            .. container:: parameters itemdetails

                *func*
                    The syntax command function.
                *args*
                    Positional arguments for the command.
                *kwargs*
                    Keyword arguments for the command.

        .. py:method:: vpe.syntax.Syntax.std_cluster(name)

            Create a standard (externally defined) cluster.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The cluster's full name.

        .. py:method:: vpe.syntax.Syntax.std_group(name)

            Create a standard (externally defined) group.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The group's full name.

        .. py:method:: vpe.syntax.Syntax.sync_group(name,**options)

            Create a sync group within this `syntax` object's namespace.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The group's name.
                *options*
                    Options for the group.

SyntaxBase
----------

.. py:class:: vpe.syntax.SyntaxBase

    Base class for various syntax support classes.

    **Static methods**

        .. py:staticmethod:: vpe.syntax.SyntaxBase.get_offsets(...)

            .. parsed-literal::

                get_offsets(
                    options: dict,
                    offset_names: Iterable[str]
                ) -> Tuple[str, dict]

            Extract the offset arguments from keyword options.


            **Parameters**

            .. container:: parameters itemdetails

                *options*: dict
                    A dictionary of options.
                *offset_names*: typing.Iterable[str]
                    The offset option names to extract.

            **Return value**

            .. container:: returnvalue itemdetails

                A tuple of the extracted offsets and the remaining options. The
                offsets value is a string of the form name=value[,...], ready to
                use in the Vim syntax command.

convert_syntax_options
----------------------

.. py:function:: vpe.syntax.convert_syntax_options(options) -> dict

    Convert values in a dictionary of option to `Option` instances.


    **Parameters**

    .. container:: parameters itemdetails

        *options*
            The dictionary containing keyword defined options.

    **Return value**

    .. container:: returnvalue itemdetails

        The same (modified in place) dictionary.

deliminate
----------

.. py:function:: vpe.syntax.deliminate(pat: str) -> str

    Put deliminators around a syntax expression.

    If reasonably sensible, a deliminator that is not part of the pattern is
    used. If this is not possible then the double quote character is used and
    any double quotes within the pattern are escaped with a backslash.

    **Parameters**

    .. container:: parameters itemdetails

        *pat*: str
            The pattern to be deliminated.

extract_keys
------------

.. py:function:: vpe.syntax.extract_keys(source_dict: dict,*keys: typing.Any) -> dict

    Extract a set of named items from a dictionary.

    Any item in *source_dict* that has a key contained in *keys* is moved to
    a new dictionary.

    **Parameters**

    .. container:: parameters itemdetails

        *source_dict*: dict
            The dictionary from which to extract the items.
        *keys*: typing.Any
            The keys for the items to extract.

    **Return value**

    .. container:: returnvalue itemdetails

        A new dictionary containing the items remove from the *source_dict*.