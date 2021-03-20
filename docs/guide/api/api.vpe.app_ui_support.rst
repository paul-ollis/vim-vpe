Module vpe.app_ui_support
=========================

.. py:module:: vpe.app_ui_support

Application level user interface support.

Currently this only works on X.Org based desktops.

AppWin
------

.. py:class:: vpe.app_ui_support.AppWin(dims_pixels,dims_cells,corners,borders,cell_size)

    Information about Vim's application window.


    **Parameters**

    .. container:: parameters itemdetails

        *dims_pixels*
            A sequence (w, h) giving the window's undecorated size in
            pixels.
        *dims_cells*
            A sequence (w, h) giving the window's undecorated size in
            character cells.
        *dims_corners*
            A sequence of pixel coordiates for the windows corners, in
            the order TL, TR, BR, BL. For TR and BR the X value is with
            repect to the right hand edge of the display. For BL and BR
            the Y value is with repect to the lower edge of the
            display.
        *borders*
            The pixel sizes of the window decoration borders in the
            order, left, right, top, bottom.
        *cell_size*
            The size of a character cell, in pixels.

    **Attributes**

        .. py:attribute:: vpe.app_ui_support.AppWin.borders

            The pixel sizes of the window decoration borders in the
            order, left, right, top, bottom.

        .. py:attribute:: vpe.app_ui_support.AppWin.cell_size

            The size of a character cell, in pixels.

        .. py:attribute:: vpe.app_ui_support.AppWin.dims_cells

            A sequence (w, h) giving the window's undecorated size in
            character cells.

        .. py:attribute:: vpe.app_ui_support.AppWin.dims_corners

            A sequence of pixel coordiates for the windows corners, in
            the order TL, TR, BR, BL. For TR and BR the X value is with
            repect to the right hand edge of the display. For BL and BR
            the Y value is with repect to the lower edge of the
            display.

        .. py:attribute:: vpe.app_ui_support.AppWin.dims_pixels

            A sequence (w, h) giving the window's undecorated size in
            pixels.

    **Properties**

        .. py:method:: vpe.app_ui_support.AppWin.columns()
            :property:

            The calculated number of columns for this window.

            This should be the same as the columns option value.

        .. py:method:: vpe.app_ui_support.AppWin.decor_dims() -> Tuple[int, int]
            :property:

            The windows dimension in pixels including window decoration.

Display
-------

.. py:class:: vpe.app_ui_support.Display(w,h,x,y)

    Information about a single display (physical screen).


    **Parameters**

    .. container:: parameters itemdetails

        *w*
            The width in pixels.
        *h*
            The height in pixels.
        *x*
            The X coordinate, in pixels, of the top left corner.
        *y*
            The Y coordinate, in pixels, of the top left corner.

    **Attributes**

        .. py:attribute:: vpe.app_ui_support.Display.h

            The height in pixels.

        .. py:attribute:: vpe.app_ui_support.Display.w

            The width in pixels.

        .. py:attribute:: vpe.app_ui_support.Display.x

            The X coordinate, in pixels, of the top left corner.

        .. py:attribute:: vpe.app_ui_support.Display.y

            The Y coordinate, in pixels, of the top left corner.

Displays
--------

.. py:class:: vpe.app_ui_support.Displays

    Information about the available displays (physical screens).


    **Attributes**

        .. py:attribute:: vpe.app_ui_support.Displays.displays

            A sequence of `Display` instances.

    **Methods**

        .. py:method:: vpe.app_ui_support.Displays.add(display)

            Add a display.

        .. py:method:: vpe.app_ui_support.Displays.find_display_for_window(w: AppWin) -> Optional[Display]

            Find which display a given `Window` is on.

            The position of the windows top-left corner is used for the
            determination.

            **Parameters**

            .. container:: parameters itemdetails

                *w*: AppWin
                    The window bein searched for.

get_app_win_info
----------------

.. py:function:: vpe.app_ui_support.get_app_win_info() -> Optional[AppWin]

    Get information about the Vim application window.

get_display_info
----------------

.. py:function:: vpe.app_ui_support.get_display_info() -> Displays

    Get information about the displays (screens).