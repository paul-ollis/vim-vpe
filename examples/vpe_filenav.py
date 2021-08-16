"""Demonstration of a simple file explorer.

When this is run it displays a file explorer in a new tab. You can choose to
open the highlighted file, by pressing the <return> key. Opening a directory
changes the display to show that directory's contents.
"""

from pathlib import Path
from typing import Iterator, Tuple, Optional

from vpe import vim, commands, mapping, syntax
import vpe


class DirView:
    """A view of a directories contents."""
    dirpath: Path

    def __init__(self, buf: vpe.Buffer):
        self.buf = buf
        self.dirs = []
        self.files = []
        with vpe.AutoCmdGroup('explorer') as grp:
            grp.delete_all()
            # grp.add('CursorMoved', func=self.on_move)
            mapping.nmap('<return>', self.on_open)
        self.mark_current()

    def on_move(self):
        """React to movement of the cursor."""
        self.mark_current()

    def on_open(self, _keys):
        """React to request to open a file."""
        name = vim.current.line
        if name == '..':
            self.load_directory(self.dirpath.parent)
            return
        path = Path(name)
        if path.is_dir():
            self.load_directory(path)
        else:
            commands.tabclose()
            commands.edit(name)

    @staticmethod
    def mark_current():
        """Mark the currently selected file."""
        row, _ = vim.current.window.cursor
        commands.match('IncSearch', rf'/\%{row}l.*/')

    def load_directory(self, dirpath: Path):
        """Read the contents of  dorectory and disply in the buffer."""
        self.dirpath = dirpath
        self.dirs[:] = sorted(p for p in dirpath.iterdir() if p.is_dir())
        self.files = sorted(p for p in dirpath.iterdir() if not p.is_dir())
        self.files[:] = [p for p in self.files if p.name[:1] != '.']
        startline = 1
        if dirpath.parent != dirpath:
            self.dirs[0:0] = ['..']
            startline = 2

        with self.buf.modifiable(), self.buf.list() as lines:
            lines[:] = [str(p) for p in self.dirs + self.files]
        vim.current.window.cursor = startline, 0
        self.set_highlighting()

    def set_highlighting(self):
        """Set up syntax highlightling for the directory list."""
        with syntax.Syntax('explorer') as syn:
            directory = syn.group('Directory')
            file = syn.group('File')
            ndirs = len(self.dirs)
            directory.add_match('^.*$', lrange=(1, ndirs))
            file.add_match('^.*$', lrange=(ndirs, ndirs + len(self.files)))

            syn.std_group('Directory').add_links(directory)
            syn.std_group('Question').add_links(file)


def iter_all_windows() -> Iterator[Tuple[vpe.TabPage, vpe.Window]]:
    """Iterate over all windows in all tab pages."""
    for page in vim.tabpages:
        for win in page.windows:
            yield page, win


def run():
    """The entry point for this script."""

    # This only needs to be true when testing.
    testing = False

    # Get the buffer used to display the directory list (it will be created if
    # necessary).
    buf: vpe.Buffer = vpe.get_display_buffer('explore')
    if testing:
        info = buf.store('explorer-status')
        if info.view:
            del info.view

    # Switch to the explorer tab page if available, otherwise create a new tab
    # page.
    page: vpe.TabPage
    win: vpe.Window
    for page, win in iter_all_windows():
        if win.buffer is buf:
            commands.tabnext(page.number)
            win.goto()
            break
    else:
        page = vpe.TabPages.new()
        commands.buffer(buf.number)

    # If the view is already attached to the buffer, use it. Otherwise create
    # and attach the view.
    info = buf.store('explorer-status')
    view: Optional[DirView] = info.view
    if view is None:
        # Creates a DirView object to maage the directory display.
        info.view = view = DirView(buf)
    view.load_directory(Path.cwd())


if __name__ == '__main__':
    run()
