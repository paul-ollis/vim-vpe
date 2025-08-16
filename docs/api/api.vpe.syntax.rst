Module vpe.syntax
=================


.. py:module:: syntax

A pythonic API for creating syntax highlighting definitions.

.. rubric:: Cluster

.. py:class:: Cluster(syn,name)

    A cluster of groups.


    **Parameters**

    .. container:: parameters itemdetails

        *syn*
            The `Syntax` instance that created this cluster.
        *name*
            A name for this cluster.

    **Methods**

        .. py:method:: add(group1: Union[Group, str],*groups: Union[Group, str])

            Add groups to the cluster.

            A group argument may be a name, in which case it references or creates
            a group within the parent `syntax` object.

            **Parameters**

            .. container:: parameters itemdetails

                *group1*: Union
                    The first group to be added.
                *groups*: Union
                    Additional groups to be added.

        .. py:method:: group(name,**options)

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

        .. py:method:: include(path_name)

            Include Vim syntax file, adding its groups to this cluster.

            This does a :vim:`syn-include` operation with a cluster name.

            **Parameters**

            .. container:: parameters itemdetails

                *path_name*
                    The path name of the syntax file to include. If this is
                    a relative path, the file is searched for within the
                    ::vim:`runtimepath`.

        .. py:method:: invoke(file=None) -> None

            Invoke any pending syntax commands.

            This is only intended to be used by a `Syntax` instance.

.. rubric:: ContainedIn

.. py:class:: ContainedIn(group: 'Group')

    A containedin option.

.. rubric:: Contains

.. py:class:: Contains(*groups: 'Group')

    Store for the syntax contains option.


    **Parameters**

    .. container:: parameters itemdetails

        *groups*: list
            This can optionally be initialised with one or more groups.

.. rubric:: End

.. py:class:: End(pat,*pats,lidx=None,lrange=None,**options)

    An end pattern.

.. rubric:: Group

.. py:class:: Group(syn,name,std=False,contained=False)

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
            automatically have the contained option set.

    .. py:class:: region_type(syn: 'Syntax',syn_cmd: Callable,name: str,**options)

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

            .. py:method:: end(pat: str,*pats: str,**kwargs) -> Region

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

            .. py:method:: matchgroup(group: Group | None)

                Add or remove a matchgroup directive for this region.

            .. py:method:: skip(pat: str,*pats: str,**kwargs) -> Region

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

            .. py:method:: start(pat: str,*pats: str,**kwargs) -> Region

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

        .. py:method:: add_keyword(keyword,*keywords,**options)

            Add one or more keywords to this syntax group.


            **Parameters**

            .. container:: parameters itemdetails

                *keyword*
                    The first keyword to add.
                *keywords*
                    Additional keywords to add.
                *options*
                    Options for the set of keywords.

        .. py:method:: add_links(*groups)

            Add groups to the set that link to this group.

        .. py:method:: add_match(...)

            .. code::

                add_match(
                        pat: str,
                        *pats: str,
                        lidx: Optional[int] = None,
                        lrange: Optional[Tuple[int, int]] = None,

            Add a syntax match for this group.


            **Parameters**

            .. container:: parameters itemdetails

                *pat*: str
                    The first part of the regular expression string.
                *pats*: str
                    Additional expression strings. These are concatenated with
                    *pat* to form the complete regular expression.
                *lidx*: Optional
                    The index of a line to tie the match to.
                *lrange*: Optional
                    A range of lines to tie the match to.
                *options*
                    Additional options for the match.

        .. py:method:: add_region(start: str,end: str,skip: Optional[str] = None,**options)

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
                *skip*: Optional
                    Optional skip pattern.
                *options*
                    Additional options for the region.

        .. py:method:: highlight(**kwargs)

            Define highlighting for this group.


            **Parameters**

            .. container:: parameters itemdetails

                *kwargs*
                    These are the same as for `vpe.highlight`, except that ``group``
                    and ``clear`` should not be  used.

        .. py:method:: invoke(file=None) -> None

            Invoke any pending syntax commands.

            This is only intended to be used by a `Syntax` instance.

        .. py:method:: region(**options)

            Create a region context manager.

            This supports regions with multiple start, skip and end patterns.

            **Parameters**

            .. container:: parameters itemdetails

                *options*
                    Additional options for the region.

        .. py:method:: set_highlight(file=None)

            Set up highlight definition for this group.

.. rubric:: GroupOption

.. py:class:: GroupOption(group: 'Group')

    Base class for group options.


    **Parameters**

    .. container:: parameters itemdetails

        *group*
            A group instance.

.. rubric:: LocationGroup

.. py:class:: LocationGroup(name,group)

    A grouphere or groupthere option.


    **Parameters**

    .. container:: parameters itemdetails

        *name*: str
            The option name - 'grouphere' or groupthere'.
        *group*
            A group instance.

.. rubric:: MatchGroup

.. py:class:: MatchGroup(group: 'Group')

    A matchgroup option.

.. rubric:: MatchGroupDirective

.. py:class:: MatchGroupDirective(group: Group | None)

    A matchgroup directive for a region.

    **Methods**

        .. py:method:: arg_str() -> str

            Format matchgroup as an directove in a region command.

.. rubric:: NamedSyntaxItem

.. py:class:: NamedSyntaxItem(syn: 'Syntax',name: str,std=False)

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

        .. py:property:: arg_name() -> str

            A suitable name when used as an argument.

        .. py:property:: name() -> str

            The base name of this item, without the Sytntax ojbect's prefix.

        .. py:property:: qual_name() -> str

            The qualified name of this item.

            It this was created with std=True then this is the same as the `name`.
            Otherwise the parent Syntax object's namespace is assed to `name` as a
            prefix.

.. rubric:: NextGroup

.. py:class:: NextGroup(group: 'Group')

    A nextgroup option.

.. rubric:: Option

.. py:class:: Option

    Base class for the syntax command options.

    **Methods**

        .. py:method:: vim_fmt() -> str

            Format the option as a string for use in a :syntax command.

.. rubric:: Pattern

.. py:class:: Pattern(pat,*pats,lidx=None,lrange=None,**options)

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

        .. py:method:: arg_str() -> str

            Format pattern as an argument to a ayntax command.

.. rubric:: Region

.. py:class:: Region(syn: 'Syntax',syn_cmd: Callable,name: str,**options)

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

        .. py:method:: end(pat: str,*pats: str,**kwargs) -> Region

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

        .. py:method:: matchgroup(group: Group | None)

            Add or remove a matchgroup directive for this region.

        .. py:method:: skip(pat: str,*pats: str,**kwargs) -> Region

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

        .. py:method:: start(pat: str,*pats: str,**kwargs) -> Region

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

.. rubric:: SimpleOption

.. py:class:: SimpleOption(name: str,value: bool)

    A simple syntax option.


    **Parameters**

    .. container:: parameters itemdetails

        *name*
            The option's name.
        *value*
            If true then the option is enabled.

    **Methods**

        .. py:method:: vim_fmt() -> str

            Format the option as a string for use in a :syntax command.

.. rubric:: Skip

.. py:class:: Skip(pat,*pats,lidx=None,lrange=None,**options)

    A skip pattern.

.. rubric:: Start

.. py:class:: Start(pat,*pats,lidx=None,lrange=None,**options)

    A start pattern.

.. rubric:: StdCluster

.. py:class:: StdCluster(syn,name)

    A cluster of groups, not in a `Syntax` object's namespace.

    **Properties**

        .. py:property:: arg_name()

            A suitable name when used as an argument.

    **Methods**

        .. py:method:: invoke() -> None

            Null operation implementation.

.. rubric:: SyncGroup

.. py:class:: SyncGroup(syn,name,std=False,contained=False)

    A group use for synchronisation.

.. rubric:: Syntax

.. py:class:: Syntax(group_prefix,clear: bool = True)

    Context manager for defining syntax highlighting.

    This stores a sequence of syntax highlighting directives. The directives
    are executed (as syntax and highlight commands) when the context is exited.

    **Parameters**

    .. container:: parameters itemdetails

        *group_prefix*
            A prefix added to the name of all groups created using this
            Syntax instance.
        *clear*
            Whether to clear any previous syntax for the current buffer.
            This is ``True`` by default.

    .. py:class:: group_type(syn,name,std=False,contained=False)

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
                automatically have the contained option set.

        .. py:class:: region_type(syn: 'Syntax',syn_cmd: Callable,name: str,**options)

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

                .. py:method:: end(pat: str,*pats: str,**kwargs) -> Region

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

                .. py:method:: matchgroup(group: Group | None)

                    Add or remove a matchgroup directive for this region.

                .. py:method:: skip(pat: str,*pats: str,**kwargs) -> Region

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

                .. py:method:: start(pat: str,*pats: str,**kwargs) -> Region

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

            .. py:method:: add_keyword(keyword,*keywords,**options)

                Add one or more keywords to this syntax group.


                **Parameters**

                .. container:: parameters itemdetails

                    *keyword*
                        The first keyword to add.
                    *keywords*
                        Additional keywords to add.
                    *options*
                        Options for the set of keywords.

            .. py:method:: add_links(*groups)

                Add groups to the set that link to this group.

            .. py:method:: add_match(...)

                .. code::

                    add_match(
                            pat: str,
                            *pats: str,
                            lidx: Optional[int] = None,
                            lrange: Optional[Tuple[int, int]] = None,

                Add a syntax match for this group.


                **Parameters**

                .. container:: parameters itemdetails

                    *pat*: str
                        The first part of the regular expression string.
                    *pats*: str
                        Additional expression strings. These are concatenated with
                        *pat* to form the complete regular expression.
                    *lidx*: Optional
                        The index of a line to tie the match to.
                    *lrange*: Optional
                        A range of lines to tie the match to.
                    *options*
                        Additional options for the match.

            .. py:method:: add_region(start: str,end: str,skip: Optional[str] = None,**options)

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
                    *skip*: Optional
                        Optional skip pattern.
                    *options*
                        Additional options for the region.

            .. py:method:: highlight(**kwargs)

                Define highlighting for this group.


                **Parameters**

                .. container:: parameters itemdetails

                    *kwargs*
                        These are the same as for `vpe.highlight`, except that ``group``
                        and ``clear`` should not be  used.

            .. py:method:: invoke(file=None) -> None

                Invoke any pending syntax commands.

                This is only intended to be used by a `Syntax` instance.

            .. py:method:: region(**options)

                Create a region context manager.

                This supports regions with multiple start, skip and end patterns.

                **Parameters**

                .. container:: parameters itemdetails

                    *options*
                        Additional options for the region.

            .. py:method:: set_highlight(file=None)

                Set up highlight definition for this group.

    .. py:class:: sync_group_type(syn,name,std=False,contained=False)

        A group use for synchronisation.

    **Methods**

        .. py:method:: cluster(name,*add_groups)

            Create a cluster within this `syntax` object's namespace.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The cluster's name.

        .. py:method:: fmt_group(name: str) -> str

            Format the name of a group, adding the Syntax object's prefix.


            **Parameters**

            .. container:: parameters itemdetails

                *name*: str
                    The name of the group.

        .. py:method:: group(name,link_to=None,**options)

            Create a group within this `syntax` object's namespace.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The group's name.
                *link_to*
                    The full name of a group to link to.
                *options*
                    Options for the group.

        .. py:method:: include(name)

            Do a simple include of syntax file.

            The command executed is: runtime syntax/name.vim

            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The syntax name.

        .. py:method:: preview_last() -> str

            Generate preview string of the last scheduled command.

            This can be useful during debugging a new syntax.

        .. py:method:: schedule(func,*args,**kwargs)

            Add a syntax command to those scheduled for later execution.


            **Parameters**

            .. container:: parameters itemdetails

                *func*
                    The syntax command function.
                *args*
                    Positional arguments for the command.
                *kwargs*
                    Keyword arguments for the command.

        .. py:method:: std_cluster(name)

            Create a standard (externally defined) cluster.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The cluster's full name.

        .. py:method:: std_group(name)

            Create a standard (externally defined) group.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The group's full name.

        .. py:method:: sync_group(name,**options)

            Create a sync group within this `syntax` object's namespace.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The group's name.
                *options*
                    Options for the group.

.. rubric:: SyntaxBase

.. py:class:: SyntaxBase

    Base class for various syntax support classes.

    **Static methods**

        .. py:staticmethod:: get_offsets(...)

            .. code::

                get_offsets(
                        options: dict,
                        offset_names: Iterable[str]

            Extract the offset arguments from keyword options.


            **Parameters**

            .. container:: parameters itemdetails

                *options*: dict
                    A dictionary of options.
                *offset_names*: Iterable
                    The offset option names to extract.

            **Return value**

            .. container:: returnvalue itemdetails

                A tuple of the extracted offsets and the remaining options. The
                offsets value is a string of the form name=value[,...], ready to
                use in the Vim syntax command.

.. rubric:: convert_syntax_options

.. py:function:: convert_syntax_options(syn,options) -> dict

    Convert values in a dictionary of option to `Option` instances.


    **Parameters**

    .. container:: parameters itemdetails

        *options*
            The dictionary containing keyword defined options.

    **Return value**

    .. container:: returnvalue itemdetails

        The same (modified in place) dictionary.

.. rubric:: deliminate

.. py:function:: deliminate(pat: str) -> str

    Put deliminators around a syntax expression.

    If reasonably sensible, a deliminator that is not part of the pattern is
    used. If this is not possible then the double quote character is used and
    any double quotes within the pattern are escaped with a backslash.

    **Parameters**

    .. container:: parameters itemdetails

        *pat*: str
            The pattern to be deliminated.

.. rubric:: extract_keys

.. py:function:: extract_keys(source_dict: dict,*keys: Any) -> dict

    Extract a set of named items from a dictionary.

    Any item in *source_dict* that has a key contained in *keys* is moved to
    a new dictionary.

    **Parameters**

    .. container:: parameters itemdetails

        *source_dict*: dict
            The dictionary from which to extract the items.
        *keys*: Any
            The keys for the items to extract.

    **Return value**

    .. container:: returnvalue itemdetails

        A new dictionary containing the items remove from the *source_dict*.
