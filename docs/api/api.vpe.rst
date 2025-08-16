Module vpe
==========

.. toctree::
    :maxdepth: 1

    api.vpe.app_ui_support
    api.vpe.argparse
    api.vpe.channels
    api.vpe.config
    api.vpe.core
    api.vpe.diffs
    api.vpe.mapping
    api.vpe.panels
    api.vpe.syntax
    api.vpe.ui
    api.vpe.windows
    api.vpe.wrappers

.. py:module:: vpe

Enhanced module for using Python 3 in Vim.

This provides the Vim class, which is a wrapper around Vim's built-in *vim*
module. It is intended that a Vim instance can be uses as a replacement for the
*vim* module. For example:

.. code-block:: py

    from vpe import vim
    # Now use 'vim' as an extended version of the *vim* module.
    # ...

The VPE module uses certain global Vim variables for its own internal purposes.
The names are chosen to be suitably obscure, but obviously associated with VPE.

_vpe_args_
    This is a dictionary that is used by a Vim function to pass information to
    Python callback functions. Predefined entries are:

    'uid'
        The unique ID for the callback function to be invoked.
    'args'
        A sequence of any unnamed arguments passed to the Vim function.

**Attributes**

    .. py:attribute:: VIM_DEFAULT

        Special value representing default Vim value for an option.


    .. py:attribute:: VI_DEFAULT

        Special value representing default Vi value for an option.


    .. py:attribute:: commands

        An object providing Vim commands as methods.

        This is an instance of the `Commands` class.


    .. py:attribute:: log

        The Vpe log support object.

        This is an instance of the `Log` class.


    .. py:attribute:: vim

        A replacement for (and wrapper around) the :vim:`python-vim` module.

        This is in instance of the `Vim` class.


.. rubric:: AutoCmdGroup

.. py:class:: AutoCmdGroup(name)

    A Pythonic way to define auto commands.

    This is a context manager that supports definition of autocommands that:

    - Are always in a given group.
    - Invoke Python code when triggered.

    It is intended to be used as:

    .. code-block:: py

        with AutoCmdGroup('mygroup') as g:
            g.delete_all()
            g.add('BufWritePre', handle_bufwrite, ...)
            g.add('BufDelete', handle_bufdelete, ...)

        ...

        # Add more autocommands to the same group.
        with AutoCmdGroup('mygroup') as g:
            g.delete_all()
            g.add('BufWritePre', handle_bufwrite, ...)

    **Parameters**

    .. container:: parameters itemdetails

        *name*
            The name of the group.

    **Static methods**

        .. py:staticmethod:: add(...)

            .. code::

                add(
                        event,
                        func,
                        pat='<buffer>',
                        once=False,
                        nested=False,

            Add a new auto command to the group.


            **Parameters**

            .. container:: parameters itemdetails

                *event*
                    The name of the event.
                *func*
                    The Python function to invoke. Plain functions and instance
                    methods are supported.
                *pat*
                    The file pattern to match. If not supplied then the special
                    '<buffer>' pattern is used. If the argument is a `Buffer` then
                    the special pattern '<buffer=N> is used.
                *once*
                    The standard ':autocmd' options.
                *nested*
                    The standard ':autocmd' options.
                *kwargs*
                    Additional keyword arguments to be passed the *func*.

        .. py:staticmethod:: delete_all()

            Delete all entries in the group.

.. rubric:: BufEventHandler

.. py:class:: BufEventHandler

    Mix-in to support mapping events to methods for buffers.

    This differs from EventHandler by the use of ``self`` as the default
    pattern.

.. rubric:: BufListener

.. py:class:: BufListener(func, buf, ops: bool = True, raw_changes: bool = False)

    An extension of `Callback` for Vim's buffer change callbacks.

    One of these is created by `Buffer.add_listener`. Direct instantiation of
    this class is not recommended or supported.

    The Python function or method to be called back.

    **Parameters**

    .. container:: parameters itemdetails

        *buf*
            The `Buffer` instance.
        *ops*
            Include the `diffs.Operation` changes as an additional argument:
        *raw_changes*
            Include the raw changes as an additional argument:


    **Attributes**

        .. py:attribute:: buf

            The `Buffer` instance.

        .. py:attribute:: listen_id

            The unique ID from a :vim:`listener_add` invocation.

        .. py:attribute:: ops

            Include the `diffs.Operation` changes as an additional argument:

        .. py:attribute:: raw_changes

            Include the raw changes as an additional argument:


    **Methods**

        .. py:method:: invoke_cb(func,vpe_args)

            Invoke this Callback.

            This extends the `Callback.invoke_cb` method.

            The vpe_args['args'] are (From Vim's docs):

            bufnr
                The buffer that was changed
            start
                First changed line number
            end
                First line number below the change
            added
                Number of lines added, negative if lines were deleted
            changes
                A List of items with details about the changes

            The ``bufnr`` is ignored, since this is just self.buf.number.

            Start and end are adjusted so they form a Python range.

            If `ops` is True then a list of operations is provided to the callback
            as an ``ops`` keyword argument. Each entry in the changes is converted
            to one of an `AddOp`, `DeleteOp` or `ChangeOp`.

            Similarly, if `raw_changes` is True
            then the list of operations provided by Vim is provided to the callback
            as a ``raw_changes`` keyword argument.

        .. py:method:: stop_listening()

            Stop listening for changes.

            This permanently disables this listener.

.. rubric:: Buffer

.. py:class:: Buffer(buffer)

    Wrapper around a :vim:`python-buffer`.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    A number of extensions to the standard :vim:`python-buffer` are provided.

    - The `vars` property provides access to the buffer's variables.
    - The `list` context manager provides a clean, and often more efficient,
      way to access the buffer's content.
    - The `temp_options` context manager provides a clean way to work with a
      buffer with some of its options temporarily modified.
    - Buffer specific meta-data can be attached using the `store`.
    - The values provided by :vim:`getbufinfo()` are effectively available as
      properties of this class.

    **Properties**

        .. py:property:: bufnr() -> int

            The same as the `number` attribute.

            This exists as a side effect of providing :vim:`getbufinfo()` values as
            properties. It is more  efficient to use the `number` attribute.

        .. py:property:: changed() -> int

            Modified flag; 0=unchanged, 1=changed.

        .. py:property:: changedtick() -> int

            Same as :vim:`changetick`.

        .. py:property:: hidden() -> int

            Hidden flag; 0=buffer visible in a window, 1=buffer hidden.

        .. py:property:: lastused() -> int

            Time (in seconds) when buffer was last used.

            This is a time in seconds as returned by :vim:`localtime()`.

        .. py:property:: linecount() -> int

            The number of lines in the buffer.

        .. py:property:: lnum() -> int

            The current line number for the buffer.

        .. py:property:: loaded() -> int

            Buffer loaded flag; 0=not loaded, 1=buffer loaded.

        .. py:property:: location() -> str

            The location of the file loaded in this buffer.

            :return:
                If the buffer is not associated with a file then an empty string.
                Otherwise the absolute directory part of the file's name.

        .. py:property:: long_display_name() -> str

            A long-form name for display purposes.

        .. py:property:: number()

            The number of this buffer.

        .. py:property:: popups() -> list[int]

            A list of window IDs for popups that are displaying this buffer.

            Each entry is a :vim:`window-ID`.

        .. py:property:: short_description() -> str

            A short description for the buffer.

            :return:
                For a quickfix window this is the title string. For a terminal this
                is the buffer's name. For other types that are associated with a
                file the `location` property is provided.

        .. py:property:: short_display_name() -> str

            A short-form name for display purposes.

        .. py:property:: type() -> str

            The type name of this buffer.

            This is similar to the :vim:`'buftype'` option, but normal buffers
            have the type 'normal'.

        .. py:property:: valid() -> bool

            Test of this buffer is valid.

            A buffer can become invalid if, for example, the underlying Vim buffer
            has been wiped out.

        .. py:property:: variables() -> Variables

            The same as the `vars` attribute.

            This exists as a side effect of providing :vim:`getbufinfo()` values as
            properties. It is more  efficient to use the `vars` attribute.

        .. py:property:: vars() -> Variables

            The buffer vars wrapped as a `Variables` instance.

        .. py:property:: windows() -> list[int]

            A list of window IDs for windows that are displaying this buffer.

            Each entry is a :vim:`window-ID`.

    **Methods**

        .. py:method:: __getattr__(name)

            Make the values from getbufinfo() available as attributes.

            This extends the base class implementation.

        .. py:method:: add_listener(...)

            .. code::

                add_listener(
                        func: ListenerCallbackFunc | ListenerCallbackMethod,
                        ops: bool = True,
                        raw_changes: bool = False

            Add a callback for changes to this buffer.

            This is implemented using :vim:`listener_add()`

            **Parameters**

            .. container:: parameters itemdetails

                *func*: Union
                    The callback function which is invoked with the following
                    arguments:

                    :buf:
                        The buffer that was changed.
                    :start:
                        Start of the range of modified lines (zero based).
                    :end:
                        End of the range of modified lines.
                    :added:
                        Number of lines added, negative if lines were deleted.

                *ops*: bool
                    ``True`` by default. Include a list of the individual operations to
                    the callback as the ``ops`` keyword argument. A list of
                    diffs.Operation instances with details about the changes.

                *raw_changes*: bool
                    ``False`` by default. Include the unmodified changes as the
                    ``raw_changes`` keyword argument (see :vim:`listener_add` for
                    details).


            **Return value**

            .. container:: returnvalue itemdetails

                A :py:obj:`BufListener` object.

        .. py:method:: append(line_or_lines,nr=None)

            Append one or more lines to the buffer.

            This is the same as using the append method of :vim:`python-buffer`.

            **Parameters**

            .. container:: parameters itemdetails

                *line_or_lines*
                    The line or lines to append.
                *nr*
                    If present then append after this line number.

        .. py:method:: clear_props()

            Remove all properties from all line in this buffer.

        .. py:method:: find_active_windows(all_tabpages=False) -> list['Window']

            Find windows where this buffer is active.

            The list windows returned is prioritised as a result of searching in
            the following order. The current window, windows in the current tab
            page, all windows in all tab pages.

            **Parameters**

            .. container:: parameters itemdetails

                *all_tabpages*
                    If True then all tab pages are searched. Otherwise only
                    the current tab page is searched.

            **Return value**

            .. container:: returnvalue itemdetails

                A list of the windows found.

        .. py:method:: find_best_active_window(all_tabpages=False) -> Window | None

            Find the best choice for a window where this buffer is active.

            This returns the first entry found by `find_active_windows`.

            **Parameters**

            .. container:: parameters itemdetails

                *all_tabpages*
                    If True (the default) all tab pages are searched.
                    Otherwise only the current tab page is searched.

            **Return value**

            .. container:: returnvalue itemdetails

                The window or None.

        .. py:method:: goto_active_window(all_tabpages=False) -> Window | None

            Goto the best choice window where this buffer is active.

            This goes to the first entry found by `find_active_windows`.

            **Parameters**

            .. container:: parameters itemdetails

                *all_tabpages*
                    If True (the default) all tab pages are searched.
                    Otherwise only the current tab page is searched.

            **Return value**

            .. container:: returnvalue itemdetails

                The window that was chosen or None.

        .. py:method:: is_active()

            Test whether the current window is showing this buffer.

        .. py:method:: list()

            A sequence context for efficient buffer modification.

            As an example:

            .. code-block:: py

                with vim.current.buffer.list() as lines:
                    # Now lines is a copy of the buffers lines.
                    lines[2:4] = ['one']  # Update lines in-place.

                # The vim.current.buffer has now been updated with modified lines.

            Although this involves taking a copy of the buffer's lines and then
            completely replacing the buffer's set of lines, this is a much more
            efficient way to make non-trivial modifications to a buffer's contents.

            This will update the buffer, even if 'modifiable' is not set.

        .. py:method:: range(a: int,b: int) -> Range

            Get a `Range` for the buffer.

            This is like getting a :vim:`python-range` object, except that it is
            wrapped in a `Range` instance.

            **Parameters**

            .. container:: parameters itemdetails

                *a*: int
                    The start index of the range.
                *b*: int
                    The end index of the range. Note that this line is included in
                    the range; *i.e.* the range is inclusive, unlike Python ranges.

        .. py:method:: retrieve_store(key: Any) -> Struct | None

            Retrieve a given buffer store if it exists.

            This is similar to `store`, but no new store is created.

            **Return value**

            .. container:: returnvalue itemdetails

                The requested store `Struct` or ``None`` if it does not exist.

        .. py:method:: set_line_prop(...)

            .. code::

                set_line_prop(
                        lidx: int,
                        start_cidx: int,
                        end_cidx: int,
                        hl_group: str,

            Set a highlighting property on a single line.

            The name of the text property is formed from the 'name' if provided and
            the 'hl_group' otherwise, by prefixing 'vpe:hl:'. For example if
            ``hl_group='Label'`` and 'name' is not provided then the property is
            called 'vpe:hl:Label'.

            The text property is created, as a buffer specific property, if it does
            not already exist. Apart from the ``bufnr`` option, default values are
            used for the property's options.

            **Parameters**

            .. container:: parameters itemdetails

                *lidx*: int
                    The index of the line to hold the property.
                *start_cidx*: int
                    The index within the line where the property starts.
                *end_cidx*: int
                    The index within the line where the property ends.
                *hl_group*: str
                    The name of the highlight group to use.
                *name*: str
                    An optional name for the property.

        .. py:method:: store(key: Any) -> Struct

            Return a `Struct` for a give key.

            This provides a mechanism to store arbitrary data associated with a
            given buffer. A new `Struct` is created the first time a given key is
            used. An example of how this can be used:

            .. code-block:: py

                vim.current.buffer.store['my-store'].processed = True
                ...
                for buf in vim.buffers:
                    if buf.store['my-store'].processed:
                        # Treat already processed buffers differently.
                        ...

            The :mod:`vpe` package arranges to return the same `Buffer` instance
            for a given :vim:`python-buffer` so this effectively allows you to
            associated meta-data with individual Vim buffers.

        .. py:method:: temp_options(**presets) -> TemporaryOptions

            Context used to temporarily change options.

            This makes it easy, for example, to use a normally unmodifiable buffer
            to display information in a buffer. To update the displayed buffer's
            contents do something like:

            .. code-block:: py

                with disp_buf.temp_options(modifiable=True):
                    disp.buf.append('Another line')

            When the context ends, the modifiable option is reset to its original
            value. An alternative approach is:

            .. code-block:: py

                with disp_buf.temp_options as opt:
                    opt.modifiable = True
                    disp.buf.append('Another line')

            Only options set using presets or the context object are restored when
            the context exits.

            **Parameters**

            .. container:: parameters itemdetails

                *presets*
                    One or more options values may be defined using keyword
                    arguments. The values are applied when the context is
                    entered.

    **Class methods**

        .. py:classmethod:: get_known(buffer: Any) -> Buffer | None

            Get the Buffer instance for a given vim.buffer.

            This is only intended for internal use.

            **Parameters**

            .. container:: parameters itemdetails

                *buffer*: Any
                    A standard :vim:`python-buffer`.

.. rubric:: Buffers

.. py:class:: Buffers(obj=None)

    Wrapper around the built-in vim.buffers.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

.. rubric:: Callback

.. py:class:: Callback(...)

    .. code::

        Callback(
                func: Callable[[...], None],
                py_args: tuple[Any, ...] = (),
                py_kwargs: dict[str, Any] | None = None,
                vim_exprs: tuple[Any, ...] = (),
                pass_bytes: bool = False,
                once: bool = False,
                cleanup: Callable[[], None] | None = None,
                meta: Any | None = None,

    Wrapper for a function to be called from Vim.

    This encapsulates the mechanism used to arrange for a Python function to
    be invoked in response to an event in the 'Vim World'. A Callback stores
    the Python function together with an ID that is uniquely associated with
    the function (the UID). If, for example this wraps function 'spam' giving
    it UID=42 then the Vim script code:

    ::

        :call VPE_Call(42, 'hello', 123)

    will result in the Python function 'spam' being invoked as:

    .. code-block:: py

        spam('hello', 123)

    The way this works is that the VPE_Call function first stores the UID
    and arguments in the global Vim variable _vpe_args_ in a dictionary
    as:

    .. code-block:: py

        {
            'uid': 42,
            'args': ['hello', 123]
        }

    Then it calls this class's `invoke` classmethod:

    ::

        return py3eval('vpe.Callback.invoke()')

    The `invoke` class method extracts the UID and uses it to find the
    Callback instance.

    Note that a strong reference to each `Callback` instance is automatically
    stored, but only while a strong reference to the function exists.

    @callbacks    A class level mapping from `uid` to `Callback` instance. This
                  is used to lookup the correct function during the execution
                  of VPE_Call.

    **Parameters**

    .. container:: parameters itemdetails

        *func*
            The Python function or method to be called back.
        *py_args*
            Addition positional arguments to be passed to *func*.
        *py_kwargs*
            Additional keyword arguments to be passed to *func*.
        *vim_exprs*
            Expressions used as positional arguments for the VPE_Call
            helper function.
        *pass_bytes*
            If true then vim byte-strings will not be decoded to Python
            strings.
        *once*
            If True then the callback will only ever be invoked once.
        *cleanup*
            If supplied then this is callable taking no arguments.
            It is invoked to perform any special clean up actions when
            the function is no longer referenced.
        *meta*
            Arbitrary meta-data to be stored in the Callback's `meta`
            attribute.
        *kwargs*
            Additional info to store with the callback. This is used
            by subclasses - see 'MapCallback' for an example.


    **Attributes**

        .. py:attribute:: call_count

            The number of times the wrapped function or method has been
            invoked.

        .. py:attribute:: meta

            Arbitrary meta-data to be stored in the Callback's `meta`
            attribute.

        .. py:attribute:: once

            If True then the callback will only ever be invoked once.

        .. py:attribute:: pass_bytes

            If true then vim byte-strings will not be decoded to Python
            strings.

        .. py:attribute:: py_args

            Addition positional arguments to be passed to *func*.

        .. py:attribute:: py_kwargs

            Additional keyword arguments to be passed to *func*.

        .. py:attribute:: uid

            The unique ID for this wrapping. It is the string form of an
            integer.

        .. py:attribute:: vim_exprs

            Expressions used as positional arguments for the VPE_Call
            helper function.

    **Methods**

        .. py:method:: as_call()

            Format a command of the form 'call VPE_Call("42", ...)'.

            The result can be used as a colon prompt command.

        .. py:method:: as_invocation()

            Format an expression of the form 'VPE_Call("42", ...)'.

            The result is a valid Vim script expression.

        .. py:method:: as_vim_function()

            Create a ``vim.Function`` that will route to this callback.

        .. py:method:: format_call_fail_message()

            Generate a message to give details of a failed callback invocation.

            This is used when the `Callback` instance exists, but the call raised
            an exception.

        .. py:method:: get_call_args(_vpe_args: Dict[str, Any])

            Get the Python positional and keyword arguments.

            This may be over-ridden by subclasses.

        .. py:method:: invoke_cb(func: Callable,vpe_args: dict)

            Invoke this Callback.

            This invokes the function as:

            .. code-block:: py

                func(*args, *vim_args, **kwargs)

            Where args and kwargs are those provided when this instance was
            created. The vim_args arr the 'args' from the vpe_args dictionary.

            **Parameters**

            .. container:: parameters itemdetails

                *vpe_args*: dict
                    A dictionary containing:

                    uid
                        The unique ID that is used to find the correct `Callback`
                        instance.
                    args
                        Any additional arguments passed to the callback by Vim.

    **Class methods**

        .. py:classmethod:: invoke() -> Any

            Invoke a particular callback function instance.

            This is invoked from the 'Vim World' by VPE_Call. The global Vim
            dictionary variable _vpe_args_ will have been set up to contain 'uid'
            and 'args' entries. The 'uid' is used to find the actual `Callback`
            instance and the 'args' is a sequence of Vim values, which are passed
            to the callback as positional arguments.

            The details are store in the Vim global variable ``_vpe_args_``, which
            is a dictionary containing:

            uid
                The unique ID that is used to find the correct `Callback` instance.
            args
                Any additional arguments passed to the callback by Vim.

            It is possible that there is no instance for the given `uid`. In that
            case a message is logged, but no other action taken.

            **Return value**

            .. container:: returnvalue itemdetails

                Normally the return value of the invoked function. If the callback
                is dead then the value is zero and if an exception is raised then
                the value is -1.

.. rubric:: CommandHandler

.. py:class:: CommandHandler

    Mix-in to support mapping user commands to methods.

    To use this do the following:

    - Make your class inherit from this class.

    - Decorate methods that implement commands using the `command` class
      method. A decorated method expect to be invoked with multiple positional
      parameters, one per command line argument.

    - In your init function, invoke ``self.auto_define_commands()``.

    Your code should only create a single instance of the class.

    **Methods**

        .. py:method:: auto_define_commands()

            Set up mappings for command methods.

    **Static methods**

        .. py:staticmethod:: command(name: str,**kwargs) -> Callable[[Callable], Callable]

            Decorator to make a user command invoke a method.


            **Parameters**

            .. container:: parameters itemdetails

                *name*: str
                    The name of the user defined command.
                *kwargs*
                    See `vpe.define_command` for the supported values.

.. rubric:: CommandInfo

.. py:class:: CommandInfo(...)

    .. code::

        CommandInfo(
                line1: int,
                line2: int,
                range: int,
                count: int,
                bang: bool,
                mods: str,

    Information passed to a user command callback handler.


    **Attributes**

        .. py:attribute:: bang

            True if the command was invoked with a '!'.

        .. py:attribute:: count

            Any count value supplied (see :vim:`command-count`).

        .. py:attribute:: line1

            The start line of the command range.

        .. py:attribute:: line2

            The end line of the command range.

        .. py:attribute:: mods

            The command modifiers (see :vim:`:command-modifiers`).

        .. py:attribute:: range

            The number of items in the command range: 0, 1 or 2 Requires at
            least vim 8.0.1089; for earlier versions this is fixed as -1.

        .. py:attribute:: reg

            The optional register, if provided.

.. rubric:: Current

.. py:class:: Current(obj=None)

    Wrapper around the built-in vim.current attribute.

.. rubric:: EventHandler

.. py:class:: EventHandler

    Mix-in to support mapping events to methods.

    This provides a convenient alternative to direct use of `AutoCmdGroup`.
    The default pattern (see :vim:`autocmd-patterns`) is '*' unless explicitly
    set by the `handle` decorator.

    **Methods**

        .. py:method:: auto_define_event_handlers(group_name: str,delete_all=False)

            Set up mappings for event handling methods.


            **Parameters**

            .. container:: parameters itemdetails

                *group_name*: str
                    The name for the auto command group (see :vim:`augrp`).
                    This will be converted to a valid Vim identifier.
                *delete_all*
                    If set then all previous auto commands in the group are
                    deleted.

    **Static methods**

        .. py:staticmethod:: handle(name: str,**kwargs) -> Callable[[Callable], Callable]

            Decorator to make an event invoke a method.


            **Parameters**

            .. container:: parameters itemdetails

                *name*: str
                    The name of the event (see :vim:`autocmd-events`.
                *kwargs*
                    See `AutoCmdGroup.add` for the supported arguments.
                    Note that the ``pat`` argument defaults to '*', not
                    '<buffer>'.

.. rubric:: Finish

.. py:class:: Finish(reason: str)

    Used by plugin's to abort installation.

    This is intended to play a similar role to the :vim:`:finish` command, as
    used in plug-ins that may not be able to complete initialisation.

    **Parameters**

    .. container:: parameters itemdetails

        *reason*
            A string providing the reason for aborting.

.. rubric:: GlobalOptions

.. py:class:: GlobalOptions(vim_options)

    Wrapper for vim.options, *etc.*

    This extends the behaviour so that options appear as attributes. The
    standard dictionary style access still works.

.. rubric:: Log

.. py:class:: Log(name: str, maxlen: int = 500, timestamps: bool = True)

    Support for logging to a display buffer.

    An instance of this class provides a mechanism to support logging that can
    be viewed within a buffer. Instances of this class act as a simple print
    function.:

    .. code-block:: py

        info = Log('my_info')
        info("Created log", info)
        info("Starting process")

    The output is stored in a Python FIFO structure, up to a maximum number of
    lines; the default is 500, change this with `set_maxlen`. No actual Vim
    buffer is created until required, which is when `show` is first
    invoked.:

    .. code-block:: py

        info.show()   # Make the log visible.

    The :mod:`vpe` module provides a predefined log, called 'VPE'. This is
    available for general use. VPE also uses it to log significant occurrences
    - mainly error conditions.

    **Parameters**

    .. container:: parameters itemdetails

        *name*
            A name that maps to the corresponding display buffer.
        *maxlen*
            The maximum number of lines to store.
        *timestamps*
            Set this to ``False`` to prevent the addition of timestamps.


    **Attributes**

        .. py:attribute:: buf

            The corresponding Vim buffer. This will be ``None`` if the `show`
            method has never been invoked.

        .. py:attribute:: name

            A name that maps to the corresponding display buffer.

    **Properties**

        .. py:property:: lines() -> list[str]

            The lines currently in the log.

            This is used by the VPE test suite. It is not really intended to
            general use and unlikely to be generally useful. Note that each access
            to this property creates a new list.

        .. py:property:: maxlen() -> int

            The current maximum length.

    **Methods**

        .. py:method:: __call__(*args)

            Write to the log.

            The arguments are formatted using ``print`` and then appended to the
            log buffer, with a time stamp.

            **Parameters**

            .. container:: parameters itemdetails

                *args*
                    The same as for Python's print function.

        .. py:method:: clear() -> None

            Clear all lines from the log.

            The FIFO is cleared and the corresponding buffer updated.

        .. py:method:: flush()

            File like I/O support.

        .. py:method:: hide() -> None

            Hide the log buffer, if showing.

        .. py:method:: redirect()

            Redirect stdout/stderr to the log.

        .. py:method:: set_maxlen(maxlen: int) -> None

            Set the maximum length of the log's FIFO.

            This will discard older lines if necessary.

            **Parameters**

            .. container:: parameters itemdetails

                *maxlen*: int
                    How many lines to store in the FIFO.

        .. py:method:: show() -> None

            Make sure the buffer is visible.

            If there is no buffer currently displayed the log then this will:

            - Split the current window.
            - Create a buffer and show it in the new split.

        .. py:method:: unredirect()

            Disable stdout/stderr redirection.

        .. py:method:: write(s)

            Write a string to the log buffer.


            **Parameters**

            .. container:: parameters itemdetails

                *s*
                    The string to write.

.. rubric:: OneShotTimer

.. py:class:: OneShotTimer(ms: int,func: Callable[[...], None])

    A version of `Timer` that can be used 'set-and-forget'.

    This version makes sure that a reference to the function and the
    `OneShotTimer` instance is saved until the timer fires. This means that
    this type of code will work:

    .. code-block:: py

        def one_shot_example():
            def fire():
                print('Bang!')
            OneShotTimer(1000, fire)

    The callback function is invoked without arguments.

    **Methods**

        .. py:method:: invoke_cb(func: Callable,vpe_args: dict)

            Invoke the callback as a result of the timer firing.

.. rubric:: Options

.. py:class:: Options(vim_options)

    Wrapper for buffer.options, *etc.*

    This extends the behaviour so that options appear as attributes. The
    standard dictionary style access still works.

.. rubric:: Popup

.. py:class:: Popup(content,name: str = '',**p_options)

    A Pythonic way to use Vim's popup windows.

    This can be used as instead of the individual functions popup_create,
    popup_hide, popup_show, popup_settext, popup_close).

    Creation of a Popup uses vim.popup_create to create the actual popup
    window. Control of the popup windows is achieved using the methods `hide`,
    `show` and `settext`. You can subclass this in order to override the
    `on_close` or `on_key` methods.

    The subclasses `PopupAtCursor`, `PopupBeval`, `PopupNotification`,
    `PopupDialog` and `PopupMenu`, provide similar convenient alternatives
    to popup_atcursor, popup_beval, popup_notification, popup_dialog and
    popup_menu.

    The windows options (line, col, pos, *etc*.) are made avaiable as
    properties of the same name. For example, to change the first displayed
    line:

    .. code-block:: py

        p = vpe.Popup(my_text)
        ...
        p.firstline += 3

    The close option must be accessed as close_control, because `close` is a
    Popup method. There is no filter or callback property.

    **Parameters**

    .. container:: parameters itemdetails

        *content*
            The content for the window.
        *name*
            An optional name for the Popup. If provided then a named
            `ScratchBuffer` is used for the content rather than letting Vim
            create one.

        *p_options*
            Vim popup_create() options can be provided as keyword
            arguments. The exceptions are filter and callback. Over ride
            the `on_key` and `on_close` methods instead.

    **Properties**

        .. py:property:: buffer() -> vpe.wrappers.Buffer | None

            The buffer holding the window's content.

            :return:
                A `Buffer` or ``None``.

        .. py:property:: id() -> int

            The ID of the Vim popup window.

    **Methods**

        .. py:method:: close(result: int = 0) -> None

            Close the popup.


            **Parameters**

            .. container:: parameters itemdetails

                *result*: int
                    The result value that will be forwarded to on_close.

        .. py:method:: hide() -> None

            Hide the popup.

        .. py:method:: move(**p_options) -> None

            Set a number of move options at once.

            An efficient way to set multiple options that affect the popup's
            position.

        .. py:method:: on_close(result: int) -> None

            Invoked when the popup is closed.

            The default implementation does nothing, it is intended that this be
            over-ridden in subclasses.

            **Parameters**

            .. container:: parameters itemdetails

                *result*: int
                    The value passed to `close`. This will be -1 if the user
                    forcefully closed the popup.

        .. py:method:: on_key(key: str,byte_seq: bytes) -> bool

            Invoked when the popup receives a keypress.

            The default implementation does nothing, it is intended that this be
            over-ridden in subclasses. The keystream is preprocessed before this
            method is invoked as follows:

            - Merged key sequences are split, so that this is always invoked
              with the sequence for just a single key.
            - Anything that does not convert to a special name is decoded to a
              Python string, if possible.
            - Special key sequences are converted to the standard Vim symbolic
              names such as <Up>, <LeftMouse>, <F11>, *etc*. Modifiers are also
              handled where possible - the modified symbolic names known to be
              available are:

              - <S-Up> <S-Down> <S-Left> <S-Right> <S-Home> <S-End> <S-Insert>
              - <C-F1> <C-F2>, *etc*.
              - <C-A> <M-A> <S-M-A> <C-M-A>, <C-B> ... <C-M-Z>

            **Parameters**

            .. container:: parameters itemdetails

                *key*: str
                    The pressed key. This is typically a single character
                    such as 'a' or a symbolic Vim keyname, such as '<F1>'.
                *byte_seq*: bytes
                    The unmodified byte sequence, as would be received for
                    a filter callback using Vimscript.

            **Return value**

            .. container:: returnvalue itemdetails

                True if the key should be considered consumed.

        .. py:method:: setoptions(**p_options) -> None

            Set a number of options at once.

            This is useful to set certain groups of options that cannot be
            separately set. For example 'textpropid' cannot be set unless
            'textprop' is set in the same popup_setoptions call.

        .. py:method:: settext(content) -> None

            Set the text of the popup.

        .. py:method:: show() -> None

            Show the popup.

    **Class methods**

        .. py:classmethod:: clear(force: bool) -> None

            Clear all popups from display.

            Use this in preference to vim.popup_clear, to ensure that VPE cleans
            up its underlying administrative structures.

            **Parameters**

            .. container:: parameters itemdetails

                *force*: bool
                    If true then if the current window is a popup, it will also be
                    closed.

.. rubric:: PopupAtCursor

.. py:class:: PopupAtCursor(content,name: str = '',**p_options)

    Popup configured to appear near the cursor.

    This creates the popup using popup_atcursor().

.. rubric:: PopupBeval

.. py:class:: PopupBeval(content,name: str = '',**p_options)

    Popup configured to appear near (v:beval_line, v:beval_col).

    This creates the popup using popup_beval().

.. rubric:: PopupDialog

.. py:class:: PopupDialog(content,name: str = '',**p_options)

    Popup configured as a dialogue.

    This creates the popup using popup_dialog(). It also provides a default
    `PopupDialog.on_key` implementation that invokes popup_filter_yesno.

    **Methods**

        .. py:method:: on_key(key,byte_seq)

            Invoke popup_filter_yesno to handle keys for this popup.

.. rubric:: PopupMenu

.. py:class:: PopupMenu(content,name: str = '',**p_options)

    Popup configured as a menu.

    This creates the popup using popup_menu(). It also provides a default
    `PopupMenu.on_key` implementation that invokes popup_filter_menu.

    **Methods**

        .. py:method:: on_key(key,byte_seq)

            Invoke popup_filter_menu to handle keys for this popup.

.. rubric:: PopupNotification

.. py:class:: PopupNotification(content,name: str = '',**p_options)

    Popup configured as a short lived notification (default 3s).

    This creates the popup in a similar manner to popup_notification.

    Note that popup_notification cannot be used because because callback
    invocation fails rather wierdly if the popup closes due to a timeout. The
    main `Popup` class provides its own timeout mechanism., which does not
    suffer from this problem.

.. rubric:: Range

.. py:class:: Range(obj=None)

    Wrapper around the built-in vim.Range type.

    User code should not directly instantiate this class.

    **Methods**

        .. py:method:: append(line_or_lines,nr=None)

            Append one or more lines to the range.

            This is the same as using the append method of :vim:`python-range`.

            **Parameters**

            .. container:: parameters itemdetails

                *line_or_lines*
                    The line or lines to append.
                *nr*
                    If present then append after this line number.

.. rubric:: Registers

.. py:class:: Registers

    Dictionary like access to the Vim registers.

    This allows Vim's registers to be read and modified. This is typically via
    the `Vim.registers` attribute.:

    .. code-block:: py

        vim.registers['a'] = 'A line of text'
        prev_copy = vim.registers[1]

    This uses :vim:`eval' to read registers and :vim:`setreg` to write them.
    Keys are converted to strings before performing the register lookup. When
    the key is the special '=' value, the un-evaluated contents of the register
    is returned.

    **Methods**

        .. py:method:: __getitem__(reg_name: str | int) -> Any

            Allow reading registers as dictionary entries.

            The reg_name may also be an integer value in the range 0-9.

        .. py:method:: __setitem__(reg_name: str | int,value: Any)

            Allow setting registers as dictionary entries.

            The reg_name may also be an integer value in the range 0-9.

.. rubric:: ScratchBuffer

.. py:class:: ScratchBuffer(name,buffer,simple_name=None)

    A scratch buffer.

    A scratch buffer has no associated file, has no swap file, never gets
    written and never appears to be modified. The content of such a buffer is
    typically under the control of plugin code. Direct editing is disabled.

    Direct instantiation is not recommended; use `get_display_buffer`, which
    creates bufferes with suitably formatted names.

    **Parameters**

    .. container:: parameters itemdetails

        *name*
            The name for the buffer.
        *buffer*
            The :vim:`python-buffer` that this wraps.
        *simple_name*
            An alternative simple name. This is used in the generation of the
            `syntax_prefix` and `auto_grp_name` property values. If this is not set
            then is is the same a the *name* parameter. If this is not a valid
            identifier then it is converted to one by replacing invalid characters
            with 'x'.

    **Attributes**

        .. py:attribute:: simple_name

            An alternative simple name. This is used in the generation of the
            `syntax_prefix` and `auto_grp_name` property values. If this is not set
            then is is the same a the *name* parameter. If this is not a valid
            identifier then it is converted to one by replacing invalid characters
            with 'x'.

    **Properties**

        .. py:property:: auto_grp_name()

            A suitable name for auto commands for this buffer.

        .. py:property:: syntax_prefix()

            A suitable prefix for syntax items in this buffer.

    **Methods**

        .. py:method:: init_options()

            Initialise the scratch buffer specific options.

            This gets invoked via call_soon because option setting can otherwise
            silently fail for subclasses.

            Subclasses may over-ride this.

        .. py:method:: modifiable() -> TemporaryOptions

            Create a context that allows the buffer to be modified.

        .. py:method:: on_first_showing()

            Invoked when the buffer is first, successfully displayed.

            This is expected to be extended (possibly over-ridden) by subclasses.

        .. py:method:: set_ext_name(name)

            Set the extension name for this buffer.


            **Parameters**

            .. container:: parameters itemdetails

                *name*
                    The extension part of the name

        .. py:method:: show(splitlines: int = 0,splitcols: int = 0) -> bool

            Make this buffer visible.

            Without a *splitlines* or *splitcols* argument, this will use the
            current window to show this buffer. Otherwise the current window is
            split, horizontally if *splitlines* != 0 or vertically if *splitcols*
            != 0. The buffer is shown in the top/left part of the split. A positive
            split specifies how many lines/columns to allocate to the bottom/right
            part of the split. A negative split specifies how many lines to
            allocate to the top/left window.

            **Parameters**

            .. container:: parameters itemdetails

                *splitlines*: int
                    Number of lines allocated to the top/bottom of the split.
                *splitcols*: int
                    Number of columns allocated to the left or right window of
                    the split.

            **Return value**

            .. container:: returnvalue itemdetails

                True if the window is successfully shown.

.. rubric:: Struct

.. py:class:: Struct

    A basic data storage structure.

    This is intended to store arbitrary name, value pairs as attributes.
    Attempting to read an undefined attribute gives ``None``.

    This is provided primarily to support the `Buffer.store` mechanism. Direct
    use of this class is not intended as part of the API.

    **Methods**

        .. py:method:: __getstate__()

            Support pickling - only intended for testing.

        .. py:method:: __setstate__(state)

            Support pickling - only intended for testing.

.. rubric:: TabPage

.. py:class:: TabPage(obj=None)

    Wrapper around a :vim:`python-tabpage`.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    This is a proxy that extends the vim.Window behaviour in various ways.

    **Properties**

        .. py:property:: vars()

            The buffar vars wrapped as a `Variables` instance.

.. rubric:: TabPages

.. py:class:: TabPages(obj=None)

    Wrapper around the built-in vim.tabpages.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    This is a proxy that extends the vim.TabPages behaviour in various ways.

    **Static methods**

        .. py:staticmethod:: new(position='after')

            Create a new tab page.


            **Parameters**

            .. container:: parameters itemdetails

                *position*
                    The position relative to this tab. The standard character prefixes
                    for the :vim:`:tabnew` command can be used or one of the more
                    readable strings:

                    'after', 'before'
                        Immediately after or before the current tab (same as '.', '-'),
                    'first', 'last'
                        As the first or last tab (same as '0', '$'),

                    This defaults to 'after'.

.. rubric:: Timer

.. py:class:: Timer(...)

    .. code::

        Timer(
                ms: int | float,
                func: Callable[[...], None],
                repeat: int | None = None,
                pass_timer: bool = True,
                meta: Any | None = None,
                args=(),

    Pythonic way to use Vim's timers.

    This can be used as a replacement for the vim functions: timer_start,
    timer_info, timer_pause, timer_stop.

    An example of usage:

    .. code-block:: py

        def handle_expire(t):
            print(f'Remaining repeats = {t.repeat}')

        # This will cause handle_expire to be called twice. The output will be:
        #     t.repeat=2
        #     t.repeat=1
        t = Timer(ms=100, handle_expire, repeat=2)

    The status of a timer can be queried using the properties `time`, `repeat`,
    `remaining` and `paused`. The methods `pause`, `stop` and `resume` allow
    an active timer to be controlled.

    A timer with ms == 0 is a special case. It is used to schedule an action to
    occur as soon as possible once Vim is waiting for user input. Consequently
    the repeat argument is forced to be 1 and the pass_timer argument is forced
    to be ``False``.

    **Parameters**

    .. container:: parameters itemdetails

        *ms*
            The timer's interval in milliseconds. The value ``int(ms)``
            is used.
        *func*
            The function to be invoked when the timer fires. This is
            called with the firing `Timer` instance as the only
            parameter.
        *repeat*
            How many times to fire. This defaults to a single firing.
        *pass_timer*
            Set this false to prevent the timer being passed to func.
        *meta*
            Arbitrary meta-data to be stored in the Callback's `meta`
            attribute.
        *args*
            Optional positional arguments to pass to func.
        *kwargs*
            Optional keyword arguments to pass to func.


    **Attributes**

        .. py:attribute:: args

            Optional positional arguments to pass to func.

        .. py:attribute:: dead

            This is set true when the timer is no longer active because
            all repeats have occurred or because the callback function is
            no longer available.

        .. py:attribute:: fire_count

            This increases by one each time the timer's callback is
            invoked.

        .. py:attribute:: kwargs

            Optional keyword arguments to pass to func.


        .. py:attribute:: meta

            Arbitrary meta-data to be stored in the Callback's `meta`
            attribute.

    **Properties**

        .. py:property:: id() -> int

            The ID of the underlying vim timer.

        .. py:property:: paused() -> bool

            True if the timer is currently paused.

        .. py:property:: remaining() -> int

            The time remaining (ms) until the timer will next fire.

        .. py:property:: repeat() -> int

            The number of times the timer will still fire.

            Note that prior to Patch 8.2.3768 this was 1 greater that one might
            expect. Now Vim's ``timer_info()`` returns the expected value except
            duruing the final callback, when we get ``None``. This is non-Pythonic,
            so ``None`` is converted to zero.

        .. py:property:: time() -> int

            The time value used to create the timer.

    **Methods**

        .. py:method:: finish()

            Take action when a timer is finished.

        .. py:method:: invoke_cb(func: Callable,vpe_args: dict)

            Invoke the callback as a result of the timer firing.

        .. py:method:: pause()

            Pause the timer.

            This invokes vim's timer_pause function.

        .. py:method:: resume()

            Resume the timer, if paused.

            This invokes vim's timer_pause function.

        .. py:method:: stop()

            Stop the timer.

            This invokes vim's timer_stop function.

.. rubric:: Variables

.. py:class:: Variables(obj=None)

    Wrapper around the various vim variable dictionaries.

    This allows entries to be modified.

.. rubric:: Vim

.. py:class:: Vim(*args,**kwargs)

    A wrapper around and replacement for the *vim* module.

    This is a instance object not a module, but it provides a API that is
    extremely compatible with the :vim:`python-vim` module.

    **Properties**

        .. py:property:: buffers() -> Buffers

            A read-only container of the all the buffers.

        .. py:property:: current() -> Current

            Convenient access to currently active objects.

            Note: Does not support assignment to window, buffer or tabpage.

        .. py:property:: error() -> Type[_vim.error]

            The plain built-in Vim exception (:vim:`python-error`).

        .. py:property:: options() -> GlobalOptions

            An object providing access to Vim's global options.

        .. py:property:: registers() -> Registers

            Dictionary like access to Vim's registers.

            This returns a `Registers` object.

        .. py:property:: tabpages() -> TabPages

            A read-only container of the all the tab pages.

        .. py:property:: vars() -> Variables

            An object providing access to global Vim variables.

        .. py:property:: vvars() -> Variables

            An object providing access to Vim (v:) variables.

        .. py:property:: windows() -> Windows

            A read-only container of the windows of the current tab page.

    **Methods**

        .. py:method:: command(cmd: str) -> None

            Execute an Ex command.


            **Parameters**

            .. container:: parameters itemdetails

                *cmd*: str
                    The Ex command to execute:


            **Exceptions raised**

            .. container:: exceptions itemdetails

                *VimError*
                    A more detailed version vim.error (:vim:`python-error`).

        .. py:method:: eval(expr: str) -> dict | list | str

            Evaluate a Vim expression.


            **Return value**

            .. container:: returnvalue itemdetails

                A dict, list or string. See :vim:`python-eval` for details.

            **Exceptions raised**

            .. container:: exceptions itemdetails

                *VimError*
                    A more detailed version vim.error (:vim:`python-error`).

        .. py:method:: temp_options(**presets) -> TemporaryOptions

            Context used to temporarily change options.

    **Static methods**

        .. py:staticmethod:: __new__(cls,*args,**kwargs)

            Ensure only a single Vim instance ever exists.

            This means that code like:

            .. code-block:: py

                myvim = vpe.Vim()

            Will result in the same object as `vpe.vim`.

        .. py:staticmethod:: iter_all_windows() -> Iterator[tuple[TabPage, Window]]

            Iterate over all the windows in all tabs.


            **Parameters**

            .. container:: parameters itemdetails

                *yield*
                    A tuple of TagPage and Window.

        .. py:staticmethod:: vim()

            Get the underlying built-in vim module.

.. rubric:: VimError

.. py:class:: VimError(error: _vim.error)

    A parsed version of vim.error.

    VPE code raises this in place of the standard vim.error exception. It is
    a subclass of vim.error, so code that handles vim.error will still work
    when converted to use the `vpe.vim` object.

    This exception attempts to parse the Vim error string to provide additional
    attributes:

    **Attributes**

        .. py:attribute:: code
            :type: int:

            The error code. This will be zero if parsing failed to extract
            the code.

        .. py:attribute:: command
            :type: str:

            The name of the Vim command that raised the error. This may be
            an empty string.

        .. py:attribute:: message
            :type: str:

            The message part, after extracting the command, error code and
            'Vim' prefix. If parsing completely fails then is simply the
            unparsed message.

.. rubric:: Window

.. py:class:: Window(window)

    Wrapper around a :vim:`python-window`.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    This is a proxy that extends the vim.Window behaviour in various ways.

    **Attributes**

        .. py:attribute:: id

            This is the window's unique ID (as obtained by :vim:`win_getid`).

    **Properties**

        .. py:property:: vars() -> Variables

            The buffar vars wrapped as a `Variables` instance.

        .. py:property:: visible_line_range() -> tuple[int, int]

            The range of buffer lines visible within this window.

            This is a Python style range.

    **Methods**

        .. py:method:: close() -> bool

            Close this window, if possible.


            **Return value**

            .. container:: returnvalue itemdetails

                True if the window was closed.

        .. py:method:: goto() -> bool

            Switch to this window, if possible.


            **Return value**

            .. container:: returnvalue itemdetails

                True if the current window was set successfully.

        .. py:method:: temp_options(**presets) -> TemporaryOptions

            Context used to temporarily change options.

            This does for a window what `Buffer.temp_options` does for buffer.

    **Static methods**

        .. py:staticmethod:: win_id_to_window(win_id: str) -> Window | None

            Return the window corresponding to a given window ID.

.. rubric:: Windows

.. py:class:: Windows(obj=None)

    Wrapper around the built-in vim.windows.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    **Parameters**

    .. container:: parameters itemdetails

        *obj*
            A :vim:`python-windows` object.

.. rubric:: saved_current_window

.. py:class:: saved_current_window

    Context manager that saves and restores the active window.

.. rubric:: saved_winview

.. py:class:: saved_winview

    Context manager that saves and restores the current window's view.

.. rubric:: temp_active_window

.. py:class:: temp_active_window(win: Window)

    Context manager that temporarily changes the active window.


    **Parameters**

    .. container:: parameters itemdetails

        *win*
            The `Window` to switch to.

.. rubric:: call_soon

.. py:function:: call_soon(func: Callable,*args: Any,**kwargs: Any)

    Arrange to call a function 'soon'.

    This uses a Vim timer with a delay of 0ms to schedule the function call.
    This means that currently executing Python code will complete *before*
    the function is invoked.

    The function is invoked as:

    .. code-block:: py

        func(*args, **kwargs)

    **Parameters**

    .. container:: parameters itemdetails

        *func*: Callable
            The function to be invoked.
        *args*: Any
            Positional arguments for the callback function.
        *kwargs*: Any
            Keyword arguments for the callback function.

.. rubric:: call_soon_once

.. py:function:: call_soon_once(token: Any,func: Callable,*args: Any,**kwargs: Any)

    Arrange to call a function 'soon', but only once.

    This is like `call_soon`, but if multiple calls with the same token are
    scheduled then only the first registed function is invoked when Vim's main
    loop regains control.

    **Parameters**

    .. container:: parameters itemdetails

        *token*: Any
            A token that identifies duplicate registered callbacks. This can
            be any object that may be a member of a set, except ``None``.
        *func*: Callable
            The function to be invoked.
        *args*: Any
            Positional arguments for the callback function.
        *kwargs*: Any
            Keyword arguments for the callback function.

.. rubric:: define_command

.. py:function:: define_command(...)

    .. code::

        define_command(
                name: str,
                func: Callable,
                nargs: int | str = 0,
                complete: str = '',
                range: bool | int | str = '',
                count: int | str = '',
                addr: str = '',
                bang: bool = False,
                bar: bool = False,
                register: bool = False,
                buffer: bool = False,
                replace: bool = True,
                pass_info: bool = True,
                args=(),

    Create a user defined command that invokes a Python function.

    When the command is executed, the function is invoked as:

    .. code-block:: py

        func(info, *args, *cmd_args, **kwargs)

    The *info* parameter is `CommandInfo` instance which carries all the meta
    information, such as the command name, range, modifiers, *etc*. The
    *cmd_args* are those provided to the command; each a string.
    The *args* and *kwargs* are those provided to this function.

    **Parameters**

    .. container:: parameters itemdetails

        *name*: str
            The command name; must follow the rules for :vim:`:command`.
        *func*: Callable
            The function that implements the command.
        *nargs*: int | str
            The number of supported arguments; must follow the rules for
            :vim:`:command-nargs`, except that integer values of 0, 1 are
            permitted.
        *complete*: str
            Argument completion mode (see :vim:`command-complete`). Does
            not currently support 'custom' or 'customlist'.
        *range*: bool | int | str
            The permitted type of range; must follow the rules for
            :vim:`:command-range`, except that the N value may be an
            integer.
        *count*: int | str
            The permitted type of count; must follow the rules for
            :vim:`:command-count`, except that the N value may be an
            integer. Use count=0 to get the same behaviour as '-count'.
        *addr*: str
            How range or count values are interpreted
            (see :vim:`:command-addr`).
        *bang*: bool
            If set then the '!' modifieer is supported (see
            :vim:`:command-bang`).
        *bar*: bool
            If set then the command may be followed by a '|' (see
            :vim:`:command-bar`).
        *register*: bool
            If set then an optional register is supported (see
            :vim:`:command-register`).
        *buffer*: bool
            If set then the command is only for the current buffer (see
            :vim:`:command-buffer`).
        *replace*: bool
            If set (the default) then 'command!' is used to replace an
            existing command of the same name.
        *pass_info*: bool
            If set then the first argument passed to func is a MappingInfo
            object. Defaults to True.
        *args*
            Additional arguments to pass to the mapped function.
        *kwargs*: dict | None
            Additional keyword arguments to pass to the mapped function.

.. rubric:: dot_vim_dir

.. py:function:: dot_vim_dir() -> str

    Return the path to the ~/.vim directory or its equivalent.


    **Return value**

    .. container:: returnvalue itemdetails

        This returns the first directory in the runtimepath option.

.. rubric:: echo_msg

.. py:function:: echo_msg(*args,soon=False)

    Like `error_msg`, but for information.


    **Parameters**

    .. container:: parameters itemdetails

        *args*
            All non-keyword arguments are converted to strings before output.
        *soon*
            If set, delay invocation until the back in the Vim main loop.

.. rubric:: error_msg

.. py:function:: error_msg(*args,soon=False)

    A print-like function that writes an error message.

    Unlike using sys.stderr directly, this does not raise a vim.error.

    **Parameters**

    .. container:: parameters itemdetails

        *args*
            All non-keyword arguments are converted to strings before output.
        *soon*
            If set, delay invocation until the back in the Vim main loop.

.. rubric:: find_buffer_by_name

.. py:function:: find_buffer_by_name(name: str) -> vpe.wrappers.Buffer | None

    Find the buffer with a given name.

    The name must be an exact match.

    **Parameters**

    .. container:: parameters itemdetails

        *name*: str
            The name of the buffer to find.

.. rubric:: get_display_buffer

.. py:function:: get_display_buffer(...)

    .. code::

        get_display_buffer(
                name: str,
                buf_class: Type[ScratchBuffer] = <class 'vpe.core.ScratchBuffer'>

    Get a named display-only buffer.

    The actual buffer name will be of the form '/[[name]]'. The buffer is
    created if it does not already exist.

    **Parameters**

    .. container:: parameters itemdetails

        *name*: str
            An identifying name for this buffer. This becomes the
            `ScratchBuffer.simple_name` attribute.

.. rubric:: highlight

.. py:function:: highlight(...)

    .. code::

        highlight(
                group: str | None = None,
                clear: bool = False,
                default: bool = False,
                link: str | None = None,
                disable: bool = False,
                debug: bool = False,
                file: TextIO = None,

    Execute a highlight command.

    This provides keyword arguments for all the command parameters. These are
    generally taken from the :vim:`:highlight` command's documentation.

    **Parameters**

    .. container:: parameters itemdetails

        *group*: str | None
            The name of the group being defined. If omitted then all other
            arguments except *clear* are ignored.

        *clear*: bool
            If set then the command ``highlight clear [<group>]`` is generated. All
            other arguments are ignored.

        *disable*: bool
            If set then the specified *group* is disabled using the command:

                ``highlight <group> NONE``

        *link*: str | None
            If set then a link command will be generated of the form:

                ``highlight link <group> <link>``.

            Other arguments are ignored.

        *default*: bool
            If set then the generated command has the form ``highlight
            default...``.

        *debug*: bool
            Print the command's arguments, for debugging use.

        *kwargs*
            The remaining keyword arguments act like the :vim:`:highlight`
            command's keyword arguments.

.. rubric:: pedit

.. py:function:: pedit(path: str,silent=True,noerrors=False)

    Edit file in the preview window.


    **Parameters**

    .. container:: parameters itemdetails

        *path*: str
            The files path.
        *silent*
            If true then run the :pedit command silently.
        *noerrors*
            If true then add '!' to suppress errors.

.. rubric:: popup_clear

.. py:function:: popup_clear(force=False)

    Convenience function that invokes `Popup.clear`.

.. rubric:: script_py_path

.. py:function:: script_py_path() -> str

    Derive a python script name from the current Vim script name.

.. rubric:: warning_msg

.. py:function:: warning_msg(*args,soon=False)

    A print-like function that writes a warning message.


    **Parameters**

    .. container:: parameters itemdetails

        *args*
            All non-keyword arguments are converted to strings before output.
        *soon*
            If set, delay invocation until the back in the Vim main loop.
