Module vpe.panels
=================

.. py:module:: vpe.panels

Simple display and control panel framework.

This is still being developed. The API and behaviour is likely to change.

The basic idea is that the contents of a buffer is divided into a sequence of
panels.:

::

    .-------------------------------------------------------------------.
    |Panel 1 contents.                                                  |
    |-------------------------------------------------------------------|
    |Panel 2 contents.                                                  |
    |                                                                   |
    |-------------------------------------------------------------------|
    |Panel 3 contents.                                                  |
    |                                                                   |
    :                                                                   :

The contents of each panel is managed by a `Panel` subclass. The panels are
managed by a `PanelViewBuffer`.

Panel
-----

.. py:class:: vpe.panels.Panel

    Part of a `PanelViewBuffer`.


    **Parameters**

    .. container:: parameters itemdetails

        *view*: PanelViewBuffer
            The parent `PanelViewBuffer`. This is set by `PanelViewBuffer` when
            a panel is added.
        *uid*: int
            A unique (within the PanelViewBuffer) for this panel.  This is set
            by `PanelViewBuffer` when a panel is added.


    **Attributes**

        .. py:attribute:: vpe.panels.Panel.content

            The formatted content of this panel as a sequence of line.
            This should only be set by the `format_contents` method.

        .. py:attribute:: vpe.panels.Panel.old_slice

            The buffer slice for previous content. This is set to ``None``
            by the ``apply_updates`` method.

            TODO: The reindex method must update this when it is not
            ``None``.

        .. py:attribute:: vpe.panels.Panel.start_lidx

            The index of this panel's first line within the buffer.

    **Properties**

        .. py:method:: vpe.panels.Panel.buf_slice()
            :property:

            A slice object to select this panel's line range.

        .. py:method:: vpe.panels.Panel.end_lidx()
            :property:

            The end index of the panel;s line range.

        .. py:method:: vpe.panels.Panel.syntax_prefix()
            :property:

            A suitable prefix for syntax items in this panel.

    **Methods**

        .. py:method:: vpe.panels.Panel.apply_syntax()

            Apply syntax highlighting for this panel.

            This may be over-ridden in subclasses that need specialised syntax
            highlighting.

            This is only called when the panel's `start_lidx` is correctly set.
            Previous panel specific syntax must be deleted by this method.

        .. py:method:: vpe.panels.Panel.apply_updates() -> bool

            Apply any changes since the last call to this method.

            This is where modifications to the underlying Vim buffer contents are
            performed.

            **Return value**

            .. container:: returnvalue itemdetails

                True if the buffer was updated.

        .. py:method:: vpe.panels.Panel.format_contents()

            Format this panel's contents.

            If the number of content lines changes then the parent view's
            `notify_size_change` method is invoked. If this results in the
            formatted contents changing then the parent view's
            `notify_content_change` method is invoked.

            This invokes the `on_format_contents` method, which is responsible for
            filling the `content` list.

        .. py:method:: vpe.panels.Panel.on_format_contents() -> None

            Format the content of this panel.

            The content is stored as a sequence of lines in the `content` property.
            This needs to be over-ridden in concrete subclasses.

        .. py:method:: vpe.panels.Panel.reindex(idx: int) -> int

            Update the line index information for this panel.

            This is invoked when a panel is first added to a `PanelViewBuffer` and
            when the `PanelViewBuffer` determines that the panel's starting line
            may have changed.

            **Parameters**

            .. container:: parameters itemdetails

                *idx*: int
                    The start line index for this panel.

            **Return value**

            .. container:: returnvalue itemdetails

                The start line index for any following panel.

        .. py:method:: vpe.panels.Panel.set_view(view: PanelViewBuffer,uid: int)

            Set the parent `PanelViewBuffer`.


            **Parameters**

            .. container:: parameters itemdetails

                *view*: PanelViewBuffer
                    The parent `PanelViewBuffer`.
                *uid*: int
                    The PanelViewBuffer unique ID for this panel.

PanelViewBuffer
---------------

.. py:class:: vpe.panels.PanelViewBuffer(*args,**kwargs)

    A `ScratchBuffer` organised as vertical sequence of panels.

    This provides support for the content of panels to be independently
    updated. The PanelView is responsible for making the buffer correctly
    reflect the content of the constituent panels.

    Each panel is responsible for notifying its parent PanelViewBuffer when
    significant changes have occurred, such as lines being added, removed or
    modified.

    **Properties**

        .. py:method:: vpe.panels.PanelViewBuffer.data()
            :property:

            The data store for this panel view.

        .. py:method:: vpe.panels.PanelViewBuffer.panels()
            :property:

            The sequence of panels for this display buffer.

    **Methods**

        .. py:method:: vpe.panels.PanelViewBuffer.add_panel(panel: Panel)

            Add a panel an the end of the panel list.

        .. py:method:: vpe.panels.PanelViewBuffer.format_panel(panel: Panel)

            Make a panel refresh itself.

        .. py:method:: vpe.panels.PanelViewBuffer.insert_panel(panel: Panel,index: int)

            Insert a panel into the panel list.

            The new panel's content must be empty.

            **Parameters**

            .. container:: parameters itemdetails

                *panel*: Panel
                    The panel to insert.
                *index*: int
                    Where to insert the panel.

        .. py:method:: vpe.panels.PanelViewBuffer.notify_content_change(panel: Panel)

            Handle notification that a panel's content has changed.


            **Parameters**

            .. container:: parameters itemdetails

                *panel*: Panel
                    The panel that has changed.

        .. py:method:: vpe.panels.PanelViewBuffer.notify_size_change()

            Handle notification that some panel's size has changed.

        .. py:method:: vpe.panels.PanelViewBuffer.on_buf_enter()

            Invoked each time the buffer is entered.

            Subclasses may extend this.

        .. py:method:: vpe.panels.PanelViewBuffer.on_reindex()

            Perform special processing when line reindexing has occurred.

            Subclasses may over-ride this.

        .. py:method:: vpe.panels.PanelViewBuffer.on_set_syntax()

            Perform special processing when syntax is defined.

            Subclasses may over-ride this.

        .. py:method:: vpe.panels.PanelViewBuffer.on_updates_applied(changes_occurred: bool)

            Perform special processing when buffer has been refreshed.

            Subclasses may over-ride this.

            **Parameters**

            .. container:: parameters itemdetails

                *changes_occurred*: bool
                    True if changes to the buffer have been made.

        .. py:method:: vpe.panels.PanelViewBuffer.remove_panel(panel: Panel)

            Remove a panel from the panel list.


            **Parameters**

            .. container:: parameters itemdetails

                *panel*: Panel
                    The panel to remove. It *must* be present.

        .. py:method:: vpe.panels.PanelViewBuffer.schedule_win_op(key,func,*args)

            Schedule an operation for when the buffer appears in a window.

can_cause_changes
-----------------

.. py:function:: vpe.panels.can_cause_changes(method)

    Decorator for `Panel` methods that can cause visible changes.