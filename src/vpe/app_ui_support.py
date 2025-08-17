"""Application level user interface support.

Currently this only works on X.Org based desktops.
"""

import re
import subprocess
from typing import Optional, Tuple

from vpe import vim

R_COORD = re.compile(r'([+-]-?\d+)([+-]-?\d+)')
R_GEOM = re.compile(r'(\d+)x(\d+)([+-]-?\d+)([+-]-?\d+)')
R_DIMS = re.compile(r'(\d+)x(\d+)')


def attach_vars(**kwargs):
    """Decorator to attach variables to a function.

    :kwargs: The names and initial values of the variables to add.
    """
    def decor(func):
        for name, value in kwargs.items():
            setattr(func, name, value)
        return func

    return decor


def _system(cmd):
    """Simple wrapper of subprocess to provide."""
    proc = subprocess.run(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False)
    return proc.returncode, proc.stdout.decode(errors='ignore')


@attach_vars(xid=None)
def _my_xwin_id():
    myself = _my_xwin_id
    if myself.xid is not None:
        return myself.xid

    myself.xid = ''
    exitcode, text = _system('xprop -root VimRegistry')
    if exitcode != 0:
        return ''                                            # pragma: no cover
    my_servername = vim.vvars.servername
    _, _, text = text.partition(' = ')
    for entry in text.split(', '):
        try:
            wid, name = entry.strip()[1:-1].split()
        except ValueError:                                   # pragma: no cover
            continue
        if name == my_servername:
            myself.xid = f'0x{wid}'
            return myself.xid
    return ''                                                # pragma: no cover


class _Coord:                          # pylint: disable=too-few-public-methods
    """A simple X/ Y coordinate."""
    def __init__(self, x, y):
        self.x = x
        self.y = y


class AppWin:
    """Information about Vim's application window.

    :@dims_pixels:  A sequence (w, h) giving the window's undecorated size in
                    pixels.
    :@dims_cells:   A sequence (w, h) giving the window's undecorated size in
                    character cells.
    :@dims_corners: A sequence of pixel coordinates for the windows corners, in
                    the order TL, TR, BR, BL. For TR and BR the X value is with
                    respect to the right hand edge of the display. For BL and
                    BR the Y value is with respect to the lower edge of the
                    display.
    :@borders:      The pixel sizes of the window decoration borders in the
                    order, left, right, top, bottom.
    :@cell_size:    The size of a character cell, in pixels.
    """
    def __init__(                          # pylint: disable=too-many-arguments
            self, dims_pixels, dims_cells, corners, borders, cell_size):
        self.dims_pixels = dims_pixels
        self.dims_cells = dims_cells
        self.corners = corners
        self.borders = borders
        self.cell_size = cell_size

    @property
    def columns(self) -> Optional[int]:
        """The calculated number of columns for this window.

        This should be the same as the columns option value.
        """
        if self.cell_size[0] != 0:
            return self.dims_pixels[0] // self.cell_size[0]
        return None                                          # pragma: no cover

    @property
    def decor_dims(self) -> Tuple[int, int]:
        """The windows dimension in pixels including window decoration."""
        a, b, c, d = self.borders
        w, h = self.dims_pixels
        return w + a + b, h + c + d


class Display:                         # pylint: disable=too-few-public-methods
    """Information about a single display (physical screen).

    :@w: The width in pixels.
    :@h: The height in pixels.
    :@x: The X coordinate, in pixels, of the top left corner.
    :@y: The Y coordinate, in pixels, of the top left corner.
    """
    def __init__(self, w, h, x, y):
        self.x, self.y = x, y
        self.w, self.h = w, h

    def contains_window(self, w) -> bool:
        """Test whether a window is fully contained by this display."""
        c = w.corners[0]
        if not self.x <= c.x < self.x + self.w:
            return False                                     # pragma: no cover
        if not self.y <= c.y < self.y + self.h:
            return False                                     # pragma: no cover
        return True


class Displays:
    """Information about the available displays (physical screens).

    @displays: A sequence of `Display` instances.
    """
    def __init__(self):
        self.displays = []

    def add(self, display):
        """Add a display."""
        self.displays.append(display)

    def find_display_for_window(self, w: AppWin) -> Optional[Display]:
        """Find which display a given `Window` is on.

        The position of the windows top-left corner is used for the
        determination.

        :w: The window being searched for.
        """
        for display in self.displays:
            if display.contains_window(w):
                return display
        return None                                          # pragma: no cover


def get_display_info() -> Displays:
    """Get information about the displays (screens)."""

    _, text = _system('xrandr')
    displays = Displays()
    for line in text.splitlines():
        line = line.strip()
        if ' connected ' in line:
            m = R_GEOM.search(line)
            args = [int(g) for g in m.groups()]
            displays.add(Display(*args))
    if displays.displays:
        return displays

    # Likely the xrandr command was not available.
    return None                                              # pragma: no cover


def get_app_win_info() -> Optional[AppWin]:
    """Get information about the Vim application window."""

    wid = _my_xwin_id()
    if not wid:
        return None                                          # pragma: no cover

    _, text = _system(f'xwininfo -id {wid}')
    w_pixels = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('Width'):
            w_pixels = int(line.split()[-1])
        if line.startswith('Height'):
            h_pixels = int(line.split()[-1])
        if line.startswith('-geometry'):
            m = R_GEOM.search(line)
            dims_cells = int(m.group(1)), int(m.group(2))
        if line.startswith('Corners'):
            corners = [_parse_corner(c) for c in line.split()[1:]]

    _, text = _system(
        f'xprop -id {wid} _NET_FRAME_EXTENTS WM_NORMAL_HINTS')
    borders = 0, 0
    cell_size = 0, 0
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('_NET_FRAME_EXTENTS(CARDINAL) = '):
            values = line.split('=')[-1].split(',')
            borders = [int(v.strip()) for v in values]
        if line.startswith('program specified resize increment: '):
            values = line.split(':')[-1].split(' by ')
            cell_size = [int(v.strip()) for v in values]

    try:
        return AppWin((
            w_pixels, h_pixels), dims_cells, corners, borders,
            cell_size)
    except NameError as e:                                   # pragma: no cover
        # Likely one of the commands was not available.
        print("Could not create application window info", e)
        return None


def _parse_corner(text):
    """Parse information about the window's corners."""
    m = R_COORD.match(text)
    xs, ys = [s.replace('--', '') for s in m.groups()]
    return _Coord(int(xs), int(ys))
