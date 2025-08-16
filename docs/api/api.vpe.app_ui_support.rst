Module vpe.app_ui_support
=========================


.. py:module:: app_ui_support

Application level user interface support.

Currently this only works on X.Org based desktops.

.. rubric:: AppWin

.. py:class:: AppWin(dims_pixels,dims_cells,corners,borders,cell_size)

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
            A sequence of pixel coordinates for the windows corners, in
            the order TL, TR, BR, BL. For TR and BR the X value is with
            respect to the right hand edge of the display. For BL and BR
            the Y value is with respect to the lower edge of the
            display.
        *borders*
            The pixel sizes of the window decoration borders in the
            order, left, right, top, bottom.
        *cell_size*
            The size of a character cell, in pixels.

    **Attributes**

        .. py:attribute:: borders

            The pixel sizes of the window decoration borders in the
            order, left, right, top, bottom.

        .. py:attribute:: cell_size

            The size of a character cell, in pixels.

        .. py:attribute:: dims_cells

            A sequence (w, h) giving the window's undecorated size in
            character cells.

        .. py:attribute:: dims_corners

            A sequence of pixel coordinates for the windows corners, in
            the order TL, TR, BR, BL. For TR and BR the X value is with
            respect to the right hand edge of the display. For BL and BR
            the Y value is with respect to the lower edge of the
            display.

        .. py:attribute:: dims_pixels

            A sequence (w, h) giving the window's undecorated size in
            pixels.

    **Properties**

        .. py:property:: columns() -> Optional[int]

            The calculated number of columns for this window.

            This should be the same as the columns option value.

        .. py:property:: decor_dims() -> Tuple[int, int]

            The windows dimension in pixels including window decoration.

.. rubric:: Display

.. py:class:: Display(w,h,x,y)

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

        .. py:attribute:: h

            The height in pixels.

        .. py:attribute:: w

            The width in pixels.

        .. py:attribute:: x

            The X coordinate, in pixels, of the top left corner.

        .. py:attribute:: y

            The Y coordinate, in pixels, of the top left corner.

    **Methods**

        .. py:method:: contains_window(w) -> bool

            Test whether a window is fully contained by this display.

.. rubric:: Displays

.. py:class:: Displays

    Information about the available displays (physical screens).


    **Attributes**

        .. py:attribute:: displays

            A sequence of `Display` instances.

    **Methods**

        .. py:method:: add(display)

            Add a display.

        .. py:method:: find_display_for_window(w: AppWin) -> Optional[Display]

            Find which display a given `Window` is on.

            The position of the windows top-left corner is used for the
            determination.

            **Parameters**

            .. container:: parameters itemdetails

                *w*: AppWin
                    The window being searched for.

.. rubric:: attach_vars

.. py:function:: attach_vars(**kwargs)

    Decorator to attach variables to a function.


    **Parameters**

    .. container:: parameters itemdetails

        *kwargs*
            The names and initial values of the variables to add.

.. rubric:: get_app_win_info

.. py:function:: get_app_win_info() -> Optional[AppWin]

    Get information about the Vim application window.

.. rubric:: get_display_info

.. py:function:: get_display_info() -> Displays

    Get information about the displays (screens).
