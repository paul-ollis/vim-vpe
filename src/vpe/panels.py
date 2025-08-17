"""Simple display and control panel framework.

This is still being developed. The API and behaviour is likely to change.

The basic idea is that the contents of a buffer is divided into a sequence of
panels.::

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
"""

import weakref
from functools import wraps

import vpe


class Panel:
    """Part of a `PanelViewBuffer`.

    :view: The parent `PanelViewBuffer`. This is set by `PanelViewBuffer` when
           a panel is added.
    :uid:  A unique (within the PanelViewBuffer) for this panel.  This is set
           by `PanelViewBuffer` when a panel is added.

    @start_lidx: The index of this panel's first line within the buffer.
    @content:    The formatted content of this panel as a sequence of line.
                 This should only be set by the `format_contents` method.
    @old_slice:  The buffer slice for previous content. This is set to ``None``
                 by the ``apply_updates`` method.

                 TODO: The reindex method must update this when it is not
                 ``None``.
    """
    view: 'PanelViewBuffer'
    uid: int

    def __init__(self):
        self.start_lidx = -1
        self.content = []
        self.old_slice = None

    @property
    def end_lidx(self):
        """The end index of the panel;s line range."""
        return self.start_lidx + len(self.content)

    @property
    def buf_slice(self):
        """A slice object to select this panel's line range."""
        return slice(self.start_lidx, self.end_lidx)

    @property
    def syntax_prefix(self):
        """A suitable prefix for syntax items in this panel."""
        return f'Syn_{self.view.simple_name}_{self.uid}_'

    def set_view(self, view: 'PanelViewBuffer', uid: int):
        """Set the parent `PanelViewBuffer`.

        :view: The parent `PanelViewBuffer`.
        :uid:  The PanelViewBuffer unique ID for this panel.
        """
        self.view = view
        self.uid = uid
        self.content = []

    def apply_updates(self) -> bool:
        """Apply any changes since the last call to this method.

        This is where modifications to the underlying Vim buffer contents are
        performed.

        :return: True if the buffer was updated.
        """
        if self.old_slice is not None:
            self.view[self.old_slice] = self.content
            self.old_slice = None
            return True
        return False

    def apply_syntax(self):
        """Apply syntax highlighting for this panel.

        This may be over-ridden in subclasses that need specialised syntax
        highlighting.

        This is only called when the panel's `start_lidx` is correctly set.
        Previous panel specific syntax must be deleted by this method.
        """

    def format_contents(self):
        """Format this panel's contents.

        If the number of content lines changes then the parent view's
        `notify_size_change` method is invoked. If this results in the
        formatted contents changing then the parent view's
        `notify_content_change` method is invoked.

        This invokes the `on_format_contents` method, which is responsible for
        filling the `content` list.
        """
        old_slice = self.buf_slice
        old_content, self.content = self.content, []
        self.on_format_contents()
        size_changed = len(old_content) != len(self.content)
        if size_changed:
            self.view.notify_size_change()
        if old_content != self.content:
            if self.old_slice is None:
                self.old_slice = old_slice
            self.view.notify_content_change(self)

    def reindex(self, idx: int) -> int:
        """Update the line index information for this panel.

        This is invoked when a panel is first added to a `PanelViewBuffer` and
        when the `PanelViewBuffer` determines that the panel's starting line
        may have changed.

        :idx:    The start line index for this panel.
        :return: The start line index for any following panel.
        """
        self.start_lidx = idx
        return idx + len(self.content)

    def on_format_contents(self) -> None:
        """Format the content of this panel.

        The content is stored as a sequence of lines in the `content` property.
        This needs to be over-ridden in concrete subclasses.
        """


def can_cause_changes(method):
    """Decorator for `Panel` methods that can cause visible changes."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        finally:
            self._make_changes_manifest()    # pylint: disable=protected-access

    return wrapper


class PanelViewBuffer(vpe.ScratchBuffer):
    """A `ScratchBuffer` organised as vertical sequence of panels.

    This provides support for the content of panels to be independently
    updated. The PanelView is responsible for making the buffer correctly
    reflect the content of the constituent panels.

    Each panel is responsible for notifying its parent PanelViewBuffer when
    significant changes have occurred, such as lines being added, removed or
    modified.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data.panels = []
        self.data.self_proxy = weakref.proxy(self)
        self.data.id_cache = set()
        self.data.syntax_update_required = True
        self.data.need_reindex = False
        self.data.syntax_invalid = False
        self.data.dirty = set()
        self.data.pending_window_ops = {}
        with vpe.AutoCmdGroup(self.auto_grp_name) as grp:
            grp.add('BufWinEnter', self.on_buf_enter, pat=self)

    @property
    def data(self):
        """The data store for this panel view."""
        return self.store('vpe_panels')

    @property
    def panels(self):
        """The sequence of panels for this display buffer."""
        return self.data.panels

    @vpe.BufEventHandler.handle('BufWinEnter')
    def _apply_pending_window_operations(self):
        """Do any operations that were blocked while the buffer was hidden."""
        for func, args in self.data.pending_window_ops.values():
            # pragma: no cover
            func(*args)

    def schedule_win_op(self, key, func, *args):
        """Schedule an operation for when the buffer appears in a window."""
        self.data.pending_window_ops[key] = (func, args)     # pragma: no cover

    def _get_panel_id(self):
        if self.data.id_cache:
            return self.data.id_cache.pop()
        return len(self.panels)

    def add_panel(self, panel: Panel):
        """Add a panel at the end of the panel list."""
        self.insert_panel(panel, len(self.panels))

    @can_cause_changes
    def insert_panel(self, panel: Panel, index: int):
        """Insert a panel into the panel list.

        The new panel's content must be empty.

        :panel: The panel to insert.
        :index: Where to insert the panel.
        """
        panel.set_view(self.data.self_proxy, self._get_panel_id())
        panel.start_lidx = self.panels[index - 1].end_lidx if index else 0
        self.panels[index:index] = [panel]
        self.data.need_reindex = True
        panel.format_contents()

    @can_cause_changes
    def remove_panel(self, panel: Panel):
        """Remove a panel from the panel list.

        :panel: The panel to remove. It *must* be present.
        """
        self.data.id_cache.add(panel.uid)
        self.panels.remove(panel)
        with self.modifiable():
            del self[panel.buf_slice]
        self.data.need_reindex = True

    @can_cause_changes
    def format_panel(self, panel: Panel):         # pylint: disable=no-self-use
        """Make a panel refresh itself."""
        panel.format_contents()

    def notify_size_change(self):
        """Handle notification that some panel's size has changed."""
        self.data.need_reindex = True

    def notify_content_change(self, panel: Panel):
        """Handle notification that a panel's content has changed.

        :panel: The panel that has changed.
        """
        self.data.dirty.add(panel)

    def _make_changes_manifest(self):
        """Try to reflect changes to content, syntax, etc."""
        if self.data.need_reindex:
            self._reindex()
            self.data.syntax_invalid = True
        if self.data.dirty:
            self._flush_panel_content_changes()
        if self.data.syntax_invalid:
            self._set_syntax()

    def _flush_panel_content_changes(self):
        """Make the buffer reflect changes to panel contents.

        When this is invoked, this may not be the buffer in the active window.
        """
        changes_occurred = False
        with self.modifiable():
            for panel in self.panels:
                if panel in self.data.dirty:
                    if panel.apply_updates():
                        changes_occurred = True
            tot_lines = self.panels[-1].buf_slice.stop
            if len(self) > 1 and len(self) > tot_lines:
                del self[tot_lines:]
        self.data.dirty.clear()
        self.on_updates_applied(changes_occurred)

    def on_buf_enter(self):
        """Invoked each time the buffer is entered.

        Subclasses may extend this.
        """
        if self.data.syntax_invalid:
            # TODO: This code may not be necessary.
            self._set_syntax()                               # pragma: no cover

    def _set_syntax(self):
        """Set the syntax highlighting for all panels.

        This will only be invoked when the current syntax highlighting is
        considered to be invalid.
        """
        with vpe.temp_active_buffer(self):
            with vpe.syntax.Syntax(self.syntax_prefix):
                pass  # Causes syntax to be cleared.
            for panel in self.panels:
                panel.apply_syntax()
            self.on_set_syntax()
        self.data.syntax_invalid = False

    def _reindex(self):
        """Update the line index information for all the panels."""
        idx = 0
        for panel in self.panels:
            idx = panel.reindex(idx)
        self.data.need_reindex = False
        self.on_reindex()

    def on_reindex(self):
        """Perform special processing when line reindexing has occurred.

        Subclasses may over-ride this.
        """

    def on_updates_applied(self, changes_occurred: bool):
        """Perform special processing when buffer has been refreshed.

        Subclasses may over-ride this.

        :changes_occurred: True if changes to the buffer have been made.
        """

    def on_set_syntax(self):
        """Perform special processing when syntax is defined.

        Subclasses may over-ride this.
        """
