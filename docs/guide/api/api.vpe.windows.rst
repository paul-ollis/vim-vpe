Module vpe.windows
==================

.. py:module:: vpe.windows

Window specific support.

This provides support for working with Vim window layouts. The intended way to
use this is to use `LayoutElement.create_from_vim_layout`. For example:

.. code-block:: py

    layout = LayoutElement.create_from_vim_layout(vim.winlayout())

The returned value will be a `LayoutRow`, `LayoutColumn` or `LayoutWindow`
window instance. Use the `type_name` class attribute when it is necessary to
know the actual type.

LayoutColumn
------------

.. py:class:: vpe.windows.LayoutColumn(elements: typing.List)

    Details of a column in a window layout.


    **Parameters**

    .. container:: parameters itemdetails

        *row*
            A list of Vim row or leaf specs.

    **Methods**

        .. py:method:: vpe.windows.LayoutColumn.adjust_width(tot_width: int)

            Adjust widths of children to match a new total width.

LayoutElement
-------------

.. py:class:: vpe.windows.LayoutElement(elements: typing.List)

    An element in a window layout.

    Each element is either a LayoutRow, LayoutColumn or a LayoutWindow.

    **Attributes**

        .. py:attribute:: vpe.windows.LayoutElement.type_name

            A class attribute used to identify the type of element.

    **Methods**

        .. py:method:: vpe.windows.LayoutElement.apply_sizes()

            Apply this layout's sizes to the actual Vim window layout.

        .. py:method:: vpe.windows.LayoutElement.describe(level=0)

            Generate a description as a sequence of lines.

            The description is intended to be user friendly. It is best not to rely
            on its format because it may change in future releases.

        .. py:method:: vpe.windows.LayoutElement.iter_windows()

            Iterate throught the leaf windows.

    **Class methods**

        .. py:classmethod:: vpe.windows.LayoutElement.create_from_vim_layout(layout)

            Create LayoutElement from the result of a winlayout() call.

LayoutRow
---------

.. py:class:: vpe.windows.LayoutRow(elements: typing.List)

    Details of a row in a window layout.


    **Parameters**

    .. container:: parameters itemdetails

        *row*
            A list of Vim column or leaf specs.

    **Methods**

        .. py:method:: vpe.windows.LayoutRow.adjust_width(tot_width: int)

            Adjust widths of children to match a new total width.

LayoutWindow
------------

.. py:class:: vpe.windows.LayoutWindow(id: int)

    Details of a window in a window layout.


    **Parameters**

    .. container:: parameters itemdetails

        *wid*
            The unique ID of the window.

    **Methods**

        .. py:method:: vpe.windows.LayoutWindow.adjust_width(tot_width: int)

            Adjust width of this window.

        .. py:method:: vpe.windows.LayoutWindow.describe(level=0)

            Generate a description as a sequence of lines.