Module vpe
==========

.. toctree::
    :maxdepth: 1

    api.vpe.commands
    api.vpe.core
    api.vpe.mapping
    api.vpe.syntax
    api.vpe.wrappers
.. py:module:: vpe

Enhanced module for using Python3 in Vim.

This provides the Vim class, which is a wrapper around Vim's built-in *vim*
module. It is intended that a Vim instance can be uses as a replacement for the
*vim* module. For example:

.. code-block:: py

    from vpe import vim
    # Now use 'vim' as an extended version of the *vim* module.
    # ...

This is compatible for versions of Vim from 8.0. It also needs Python 3.6 or
newer.

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

    .. py:attribute:: vpe.log

        The Vpe log support object.

        This is an instance of the `Log` class.


    .. py:attribute:: vpe.vim

        A replacement for (and wrapper around) the :vim:`python-vim` module.

        This is in instance of the `Vim` class.


AutoCmdGroup
------------

.. py:class:: vpe.AutoCmdGroup(name)

    A Pythonic way to define auto commands.

    This is a context manager that supports definition of autocommands
    that:

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

        .. py:staticmethod:: vpe.AutoCmdGroup.add(event,func,pat='<buffer>',once=False,nested=False)

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
                    the special pattern for 'buffer=N> is used.
                *once*
                    The standard ':autocmd' options.
                *nested*
                    The standard ':autocmd' options.

        .. py:staticmethod:: vpe.AutoCmdGroup.delete_all()

            Delete all entries in the group.

Buffer
------

.. py:class:: vpe.Buffer(buffer)

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

        .. py:method:: vpe.Buffer.bufnr() -> int
            :property:

            The same as the `number` attribute.

            This exists as a side effect of providing :vim:`getbufinfo()` values as
            properties. It is more  efficient to use the `number` attribute.

        .. py:method:: vpe.Buffer.changed() -> int
            :property:

            Hidden flag; 0=buffer visible in a window, 1=buffer hidden.

        .. py:method:: vpe.Buffer.changedtick() -> int
            :property:

            Same as :vim:`changetick`.

        .. py:method:: vpe.Buffer.lastused() -> int
            :property:

            Time (in seconds) when buffer was last used.

            This is a time in seconds a returned by :vim:`localtime()`.

        .. py:method:: vpe.Buffer.linecount() -> int
            :property:

            The number of lines in the buffer.

        .. py:method:: vpe.Buffer.lnum() -> int
            :property:

            The current line number for the buffer.

        .. py:method:: vpe.Buffer.loaded() -> int
            :property:

            Buffer loaded flag; 0=not loaded, 1=buffer loaded.

        .. py:method:: vpe.Buffer.location() -> str
            :property:

            The location of the file loaded in this buffer.

            :return:
                If the buffer is not associated with a file then an empty string.
                Otherwise the absolute directory part of the file's name.

        .. py:method:: vpe.Buffer.long_display_name() -> str
            :property:

            A long-form name for display purposes.

        .. py:method:: vpe.Buffer.number()
            :property:

            The number of this buffer.

        .. py:method:: vpe.Buffer.popups() -> int
            :property:

            A list windows displaying this buffer.

            Each entry is a :vim:`window-ID`.

        .. py:method:: vpe.Buffer.short_description() -> str
            :property:

            A short description for the buffer.

            :return:
                For a quickfix window this is the title string. For a terminal this
                is the buffer's name. For other types that are associated with a
                file the `location` property is provided.

        .. py:method:: vpe.Buffer.short_display_name() -> str
            :property:

            A short-form name for display purposes.

        .. py:method:: vpe.Buffer.type() -> str
            :property:

            The type name of this buffer.

            This is similar to the :vim:`'buftype'` option, but normal buffers
            have the type 'normal'.

        .. py:method:: vpe.Buffer.valid() -> bool
            :property:

            Test of this buffer is valid.

            A buffer can become invalid if, for example, the underlying Vim buffer
            has been wiped out.

        .. py:method:: vpe.Buffer.variables() -> int
            :property:

            The same as the `vars` attribute.

            This exists as a side effect of providing :vim:`getbufinfo()` values as
            properties. It is more  efficient to use the `vars` attribute.

        .. py:method:: vpe.Buffer.vars() -> Variables
            :property:

            The buffar vars wrapped as a `Variables` instance.

        .. py:method:: vpe.Buffer.windows() -> int
            :property:

            A list popup windows displaying this buffer.

            Each entry is a :vim:`window-ID`.

    **Methods**

        .. py:method:: vpe.Buffer.__getattr__(name)

            Make the values from getbufinfo() available as attributes.

            This extends the base class implementation.

        .. py:method:: vpe.Buffer.append(line_or_lines,nr=None)

            Append one or more lines to the buffer.

            This is the same as using the append method of :vim:`python-buffer`.

            **Parameters**

            .. container:: parameters itemdetails

                *line_or_lines*
                    The line or lines to append.
                *nr*
                    If present then append after this line number.

        .. py:method:: vpe.Buffer.goto_active_window() -> bool

            Goto a window where this buffer is active.

            Windows are search in the following order. The current window, windows
            in the current tab page, all windows in all tab pages.

            This has no effect (and returns False) if the buffer is not active in
            any window.

            **Return value**

            .. container:: returnvalue itemdetails

                True if an active window was found

        .. py:method:: vpe.Buffer.list()

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

        .. py:method:: vpe.Buffer.range(a: int,b: int) -> Range

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

        .. py:method:: vpe.Buffer.store(key: typing.Any) -> Struct

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

        .. py:method:: vpe.Buffer.temp_options(**presets) -> TemporaryOptions

            Context used to temporarily change options.

            This makes it easy, for example, to use a normally unmodifiable buffer
            to display information in a buffer. To update the displayed buffer's
            contents do something like:

            .. code-block:: py

                with disp_buf.temp_options(modifiable=True):
                    disp.buf.append('Another line')

            When the context ends, the modifiable option is reset to its original
            value. An alterative approach is:

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

        .. py:classmethod:: vpe.Buffer.get_known(buffer: typing.Any) -> Optional[ForwardRef('Buffer')]

            Get the Buffer instance for a given vim.buffer.

            This is only intended for internal use.

            **Parameters**

            .. container:: parameters itemdetails

                *buffer*: typing.Any
                    A standard :vim:`python-buffer`.

Buffers
-------

.. py:class:: vpe.Buffers(obj=None)

    Wrapper around the built-in vim.buffers.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    This is a proxy that extends the vim.Buffer behaviour in various ways.

Current
-------

.. py:class:: vpe.Current(obj=None)

    Wrapper around the built-in vim.current attribute.

GlobalOptions
-------------

.. py:class:: vpe.GlobalOptions(vim_options)

    Wrapper for vim.options, *etc.*

    This extends the behaviour so that options appear as attributes. The
    standard dictionary style access still works.

Log
---

.. py:class:: vpe.Log(name,maxlen=500)

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


    **Attributes**

        .. py:attribute:: vpe.Log.buf

            The corresponding Vim buffer. This will be ``None`` if the `show`
            method has never been invoked.

        .. py:attribute:: vpe.Log.name

            A name that maps to the corresponding display buffer.

    **Methods**

        .. py:method:: vpe.Log.__call__(*args)

            Write to the log.

            The arguments are formatted using ``print`` and then appended to the
            log buffer, with a time stamp.

            **Parameters**

            .. container:: parameters itemdetails

                *args*
                    The same as for Python's print function.

        .. py:method:: vpe.Log.clear() -> None

            Clear all lines from the log.

            The FIFO is cleared and the corresponding buffer updated.

        .. py:method:: vpe.Log.flush()

            File like I/O support.

        .. py:method:: vpe.Log.redirect()

            Redirect stdout/stderr to the log.

        .. py:method:: vpe.Log.set_maxlen(maxlen: int) -> None

            Set the maximum length of the log's FIFO.

            This will discard older lines if necessary.

            **Parameters**

            .. container:: parameters itemdetails

                *maxlen*: int
                    How many lines to store in the FIFO.

        .. py:method:: vpe.Log.show() -> None

            Make sure the buffer is visible.

            If there is no buffer currently displayed the log then this will:

            - Split the current window.
            - Create a buffer and show it in the new split.

        .. py:method:: vpe.Log.unredirect()

            Undo most recent redirection.

        .. py:method:: vpe.Log.write(s)

            Write a string to the log buffer.


            **Parameters**

            .. container:: parameters itemdetails

                *s*
                    The string to write.

Popup
-----

.. py:class:: vpe.Popup(content,**p_options)

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
    properties of the same name. For example, to change the first displated
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
        *p_options*
            Nearly all the standard popup_create options (line, col, pos
            *etc*. can be provided as keyword arguments. The exceptions
            are filter and callback. Over ride the `on_key` and `on_close`
            methods instead.

    **Properties**

        .. py:method:: vpe.Popup.buffer() -> `Buffer`
            :property:

            The buffer holding the window's content.

        .. py:method:: vpe.Popup.id() -> int
            :property:

            The ID of the Vim popup window.

    **Methods**

        .. py:method:: vpe.Popup.close(result: int = 0) -> None

            Close the popup.


            **Parameters**

            .. container:: parameters itemdetails

                *result*: int
                    The result value that will be forwarded to on_close.

        .. py:method:: vpe.Popup.hide() -> None

            Hide the popup.

        .. py:method:: vpe.Popup.on_close(result: int) -> None

            Invoked when the popup is closed.

            The default implementation does nothing, it is intended that this be
            over-ridden in subclasses.

            **Parameters**

            .. container:: parameters itemdetails

                *result*: int
                    The value passed to `close`. This will be -1 if the user
                    forcefully closed the popup.

        .. py:method:: vpe.Popup.on_key(key: str,byte_seq: bytes) -> bool

            Invoked when the popup receives a keypress.

            The default implementation does nothing, it is intended that this be
            over-ridden in subclasses. The keystream is preprocessed before this
            is method is invoked as follows:

            - Merged key sequences are split, so that this is always invoked
              with the sequence for just a single key.
            - Special key sequences are converted to the standard Vim symbolic
              names such as <Up>, <LeftMouse>, <F11>, <S-F3>, <C-P>, *etc*.
            - Anything that does not convert to a special name is decoded to a
              Python string, if possible.

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

        .. py:method:: vpe.Popup.settext(content) -> None

            Set the text of the popup.

        .. py:method:: vpe.Popup.show() -> None

            Show the popup.

    **Class methods**

        .. py:classmethod:: vpe.Popup.clear(force: bool) -> None

            Clear all popups from display.

            Use this in preference to vim.popup_clear, to ensure that VPE cleans
            up its underlying administrative structures.

            **Parameters**

            .. container:: parameters itemdetails

                *force*: bool
                    If true then if the current window is a popup, it will also be
                    closed.

PopupAtCursor
-------------

.. py:class:: vpe.PopupAtCursor(content,**p_options)

    Popup configured to appear near the cursor.

    This creates the popup using popup_atcursor().

PopupBeval
----------

.. py:class:: vpe.PopupBeval(content,**p_options)

    Popup configured to appear near (v:beval_line, v:beval_col).

    This creates the popup using popup_beval().

PopupDialog
-----------

.. py:class:: vpe.PopupDialog(content,**p_options)

    Popup configured as a dialogue.

    This creates the popup using popup_dialog(). It also provides a default
    `PopupDialog.on_key` implementation that invokes popup_filter_yesno.

    **Methods**

        .. py:method:: vpe.PopupDialog.on_key(key,byte_seq)

            Invoke popup_filter_yesno to handle keys for this popup.

PopupMenu
---------

.. py:class:: vpe.PopupMenu(content,**p_options)

    Popup configured as a menu.

    This creates the popup using popup_menu(). It also provides a default
    `PopupMenu.on_key` implementation that invokes popup_filter_menu.

    **Methods**

        .. py:method:: vpe.PopupMenu.on_key(key,byte_seq)

            Invoke popup_filter_menu to handle keys for this popup.

PopupNotification
-----------------

.. py:class:: vpe.PopupNotification(content,**p_options)

    Popup configured as a short lived notification (default 3s).

    This creates the popup using popup_notification().

Range
-----

.. py:class:: vpe.Range(obj=None)

    Wrapper around the built-in vim.Range type.

    User code should not directly instantiate this class.

    **Methods**

        .. py:method:: vpe.Range.append(line_or_lines,nr=None)

            Append one or more lines to the range.

            This is the same as using the append method of :vim:`python-range`.

            **Parameters**

            .. container:: parameters itemdetails

                *line_or_lines*
                    The line or lines to append.
                *nr*
                    If present then append after this line number.

Registers
---------

.. py:class:: vpe.Registers

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

        .. py:method:: vpe.Registers.__getitem__(reg_name: Union[str, int]) -> typing.Any

            Allow reading registers as dictionary entries.

            The reg_name may also be an integer value in the range 0-9.

        .. py:method:: vpe.Registers.__setitem__(reg_name: Union[str, int],value: typing.Any)

            Allow setting registers as dictionary entries.

            The reg_name may also be an integer value in the range 0-9.

ScratchBuffer
-------------

.. py:class:: vpe.ScratchBuffer(name,buffer)

    A scratch buffer.

    A scratch buffer has no associated file, has no swap file, never gets
    written and never appears to be modified. The content of such a buffer is
    typically under the control of plugin code. Direct editing is disabled.

    Direct instantiation is not recommended; use `get_display_buffer`, which
    creates bufferes with suitably formatted names.

    **Methods**

        .. py:method:: vpe.ScratchBuffer.modifiable() -> TemporaryOptions

            Create a context that allows the buffer to be modified.

        .. py:method:: vpe.ScratchBuffer.show(splitlines: Optional[int] = None) -> bool

            Make this buffer visible.

            Without a splitlines argument, this will use the current window to show
            this buffer. If the *splitlines* argument is provided and greater than
            zero then:

            1. The current window is split.
            2. The lower split is set to be *splitlines* high.
            3. This buffer is displayed in the upper window.

            **Parameters**

            .. container:: parameters itemdetails

                *splitlines*: typing.Optional[int]
                    Number of lines to leave in the bottom window.

            **Return value**

            .. container:: returnvalue itemdetails

                True if the window is successfully split.

Struct
------

.. py:class:: vpe.Struct

    A basic data storage structure.

    This is intended to store arbitrary name, value pairs as attributes.
    Attempting to read an undefined attribute gives ``None``.

    This is provided primarily to support the `Buffer.store` mechanism. Direct
    use of this class is not intended as part of the API.

    **Methods**

        .. py:method:: vpe.Struct.__getstate__()

            Support pickling - only intended for testing.

        .. py:method:: vpe.Struct.__setstate__(state)

            Support pickling - only intended for testing.

TabPage
-------

.. py:class:: vpe.TabPage(obj=None)

    Wrapper around a :vim:`python-tabpage`.

    User code should not directly instantiate this class.
    This is a proxy that extends the vim.Window behaviour in various ways.

    **Properties**

        .. py:method:: vpe.TabPage.vars()
            :property:

            The buffar vars wrapped as a `Variables` instance.

TabPages
--------

.. py:class:: vpe.TabPages(obj=None)

    Wrapper around the built-in vim.tabpages.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    This is a proxy that extends the vim.TabPages behaviour in various ways.

    **Static methods**

        .. py:staticmethod:: vpe.TabPages.new(position='after')

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

Timer
-----

.. py:class:: vpe.Timer(ms,func,repeat=None)

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

    **Parameters**

    .. container:: parameters itemdetails

        *ms*
            The timer's interval in milliseconds.
        *func*
            The function to be invoked when the timer fires. This is
            called with the firing `Timer` instance as the only parameter.
        *repeat*
            How many times to fire.

    **Properties**

        .. py:method:: vpe.Timer.id() -> int
            :property:

            The ID of the underlying vim timer.

        .. py:method:: vpe.Timer.paused() -> bool
            :property:

            True if the timer is currently paused.

        .. py:method:: vpe.Timer.remaining() -> int
            :property:

            The time remaining (ms) until the timer will next fire.

        .. py:method:: vpe.Timer.repeat() -> int
            :property:

            The number of times the timer will still fire.

        .. py:method:: vpe.Timer.time() -> int
            :property:

            The time value used to create the timer.

    **Methods**

        .. py:method:: vpe.Timer.pause()

            Pause the timer.

            This invokes vim's timer_pause funciton.

        .. py:method:: vpe.Timer.resume()

            Resume the timer, if paused.

            This invokes vim's timer_pause funciton.

        .. py:method:: vpe.Timer.stop()

            Stop the timer.

            This invokes vim's timer_stop function.

    **Class methods**

        .. py:classmethod:: vpe.Timer.stop_all()

            Stop all timers and clean up.

            Use this in preference to vim.timer_stopall, to ensure that VPE cleans
            up its underlying administrative structures.

Variables
---------

.. py:class:: vpe.Variables(obj=None)

    Wrapper around the various vim variable dictionaries.

    This allows entries to be modified.

Vim
---

.. py:class:: vpe.Vim(*args,**kwargs)

    A wrapper around and replacement for the *vim* module.

    This is a instance object not a module, but it provides a API that is
    extremely compatible with the :vim:`python-vim` module.

    **Properties**

        .. py:method:: vpe.Vim.buffers() -> Buffers
            :property:

            A read-only container of the all the buffers.

        .. py:method:: vpe.Vim.current() -> Current
            :property:

            Convenient access to currently active objects.

            Note: Does not support assigment to window, buffer or tabpage.

        .. py:method:: vpe.Vim.error() -> Type[vim.error]
            :property:

            The plain built-in Vim exception (:vim:`python-error`).

        .. py:method:: vpe.Vim.options() -> GlobalOptions
            :property:

            An object providing access to Vim's global options.

        .. py:method:: vpe.Vim.registers() -> `Registers`
            :property:

            Dictionary like access to Vim's registers.

            This returns a `Registers` object.

        .. py:method:: vpe.Vim.tabpages() -> TabPages
            :property:

            A read-only container of the all the tab pages.

        .. py:method:: vpe.Vim.vars() -> Variables
            :property:

            An object providing access to global Vim variables.

        .. py:method:: vpe.Vim.vvars() -> Variables
            :property:

            An object providing access to Vim (v:) variables.

        .. py:method:: vpe.Vim.windows() -> Windows
            :property:

            A read-only container of the windows of the current tab page.

    **Methods**

        .. py:method:: vpe.Vim.command(cmd: str) -> None

            Execute an Ex command.


            **Parameters**

            .. container:: parameters itemdetails

                *cmd*: str
                    The Ex command to execute:


            **Exceptions raised**

            .. container:: exceptions itemdetails

                *VimError*
                    A more detailed version vim.error (:vim:`python-error`).

        .. py:method:: vpe.Vim.eval(expr: str) -> Union[dict, list, str]

            Evaluate a Vim expression.


            **Return value**

            .. container:: returnvalue itemdetails

                A dict, list or string. See :vim:`python-eval` for details.

            **Exceptions raised**

            .. container:: exceptions itemdetails

                *VimError*
                    A more detailed version vim.error (:vim:`python-error`).

        .. py:method:: vpe.Vim.temp_options(**presets) -> TemporaryOptions

            Context used to temporarily change options.

    **Static methods**

        .. py:staticmethod:: vpe.Vim.__new__(cls,*args,**kwargs)

            Ensure only a single Vim instance ever exists.

            This means that code like:

            .. code-block:: py

                myvim = vpe.Vim()

            Will result in the same object as `vpe.vim`.

        .. py:staticmethod:: vpe.Vim.vim()

            Get the underlying built-in vim module.

VimError
--------

.. py:class:: vpe.VimError(error: vim.error)

    A parsed version of vim.error.

    VPE code raises this in place of the standard vim.error exception. It is
    a subclass of vim.error, so code that handles vim.error will still work
    when converted to use the `vpe.vim` object.

    This exception attempts to parse the Vim error string to provide additional
    attributes:

    **Attributes**

        .. py:attribute:: vpe.VimError.code
            :type: int:

            The error code. This will be zero if parsing failed to extract
            the code.

        .. py:attribute:: vpe.VimError.command
            :type: str:

            The name of the Vim command that raised the error. This may be
            an empty string.

        .. py:attribute:: vpe.VimError.message
            :type: str:

            The message part, after extracting the command, error code and
            'Vim' prefix. If parsing completely fails then is simply the
            unparsed message.

Window
------

.. py:class:: vpe.Window(window)

    Wrapper around a :vim:`python-window`.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    This is a proxy that extends the vim.Window behaviour in various ways.

    **Properties**

        .. py:method:: vpe.Window.vars() -> Variables
            :property:

            The buffar vars wrapped as a `Variables` instance.

    **Methods**

        .. py:method:: vpe.Window.goto() -> bool

            Switch to this window, if possible.


            **Return value**

            .. container:: returnvalue itemdetails

                True if the current window was set successfully.

        .. py:method:: vpe.Window.temp_options(**presets) -> TemporaryOptions

            Context used to temporarily change options.

            This does for a window what `Buffer.temp_options` does for buffer.

Windows
-------

.. py:class:: vpe.Windows(obj=None)

    Wrapper around the built-in vim.windows.

    User code should not directly instantiate this class. VPE creates and
    manages instances of this class as required.

    **Parameters**

    .. container:: parameters itemdetails

        *obj*
            A :vim:`python-windows` object.

saved_winview
-------------

.. py:class:: vpe.saved_winview

    Context manager that saves and restores the current window's view.

call_soon
---------

.. py:function:: vpe.call_soon(func)

    Arrange to call a function 'soon'.

    This uses a Vim timer with a delay of 0ms to schedule the function call.
    This means that currently executing Python code will complete *before*
    the function is invoked.

    **Parameters**

    .. container:: parameters itemdetails

        *func*
            The function to be invoked. It takes no arguments.

error_msg
---------

.. py:function:: vpe.error_msg(*args)

    A print-like function that writes an error message.

    Unlike using sys.stderr directly, this does not raise a vim.error.

find_buffer_by_name
-------------------

.. py:function:: vpe.find_buffer_by_name(name: str) -> Optional[Buffer]

    Find the buffer with a given name.

    The name must be an exact match.

    **Parameters**

    .. container:: parameters itemdetails

        *name*: str
            The name of the buffer to find.

get_display_buffer
------------------

.. py:function:: vpe.get_display_buffer(name: str) -> ScratchBuffer

    Get a named display-only buffer.

    The actual buffer name will be of the form '/[[name]]'. The
    buffer is created if it does not already exist.

    **Parameters**

    .. container:: parameters itemdetails

        *name*: str
            An identifying name for this buffer.

highlight
---------

.. py:function:: vpe.highlight(...)

    .. parsed-literal::

        highlight(
            \*,
            group=None,
            clear=False,
            default=False,
            link=None,
            disable=False,
            \*\*kwargs)

    Python version of the highlight command.

    This provides keyword arguments for all the command parameters. These are
    generally taken from the :vim:`:highlight` command's documentation.

    **Parameters**

    .. container:: parameters itemdetails

        *group*
            The name of the group being defined. If omitted then all other
            arguments except *clear* are ignored.

        *clear*
            If set then the command ``highlight clear [<group>]`` is generated. All
            other arguments are ignored.

        *disable*
            If set then the specified *group* is disabled using the command:

                ``highlight <group> NONE``

        *link*
            If set then a link command will be generated of the form:

                ``highlight link <group> <link>``.

            Other arguments are ignored.

        *default*
            If set then the generated command has the form ``highlight
            default...``.

        *kwargs*
            The remain keyword arguments act like the :vim:`:highlight` command's
            keyword arguments.

pedit
-----

.. py:function:: vpe.pedit(path: str,silent=True,noerrors=False)

    Edit file in the preview window.


    **Parameters**

    .. container:: parameters itemdetails

        *path*: str
            The files path.
        *silent*
            If true then run the :pedit command silently.
        *noerrors*
            If true then add '!' to suppress errors.

popup_clear
-----------

.. py:function:: vpe.popup_clear(force=False)

    Convenience function that invokes `Popup.clear`.

script_py_path
--------------

.. py:function:: vpe.script_py_path() -> str

    Derive a python script name from the current Vim script name.

timer_stopall
-------------

.. py:function:: vpe.timer_stopall()

    Convenience function that invokes `Timer.stop_all`.