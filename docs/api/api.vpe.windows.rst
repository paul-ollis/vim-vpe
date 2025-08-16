Module vpe.windows
==================


.. py:module:: windows

Window specific support.

This provides support for working with Vim window layouts. The intended way to
use this is to use `LayoutElement.create_from_vim_layout`. For example:

.. code-block:: py

    layout = LayoutElement.create_from_vim_layout(vim.winlayout())

The returned value will be a `LayoutRow`, `LayoutColumn` or `LayoutWindow`
window instance. Use the `type_name` class attribute when it is necessary to
know the actual type.

.. rubric:: LayoutColumn

.. py:class:: LayoutColumn(elements: List)

    Details of a column in a window layout.


    **Parameters**

    .. container:: parameters itemdetails

        *row*
            A list of Vim row or leaf specs.

    **Properties**

        .. py:property:: width()

            The width of this column.

    **Methods**

        .. py:method:: adjust_width(tot_width: int)

            Adjust widths of children to match a new total width.

.. rubric:: LayoutElement

.. py:class:: LayoutElement(elements: List)

    An element in a window layout.

    Each element is either a LayoutRow, LayoutColumn or a LayoutWindow.

    **Attributes**

        .. py:attribute:: type_name

            A class attribute used to identify the type of element.

    **Methods**

        .. py:method:: apply_sizes()

            Apply this layout's sizes to the actual Vim window layout.

        .. py:method:: describe(level=0)

            Generate a description as a sequence of lines.

            The description is intended to be user friendly. It is best not to rely
            on its format because it may change in future releases.

        .. py:method:: iter_windows()

            Iterate through the leaf windows.

        .. py:method:: set_widths_from_layout(layout: LayoutElement)

            Update the widths using another layout element.


            **Parameters**

            .. container:: parameters itemdetails

                *layout*: LayoutElement
                    The `LayoutElement` to copy from.

    **Class methods**

        .. py:classmethod:: create_from_vim_layout(layout)

            Create LayoutElement from the result of a winlayout() call.

.. rubric:: LayoutRow

.. py:class:: LayoutRow(elements: List)

    Details of a row in a window layout.


    **Parameters**

    .. container:: parameters itemdetails

        *row*
            A list of Vim column or leaf specs.

    **Properties**

        .. py:property:: width()

            The width of this row.

    **Methods**

        .. py:method:: adjust_width(tot_width: int)

            Adjust widths of children to match a new total width.

.. rubric:: LayoutWindow

.. py:class:: LayoutWindow(win_id: int)

    Details of a window in a window layout.


    **Parameters**

    .. container:: parameters itemdetails

        *wid*
            The unique ID of the window.

    **Properties**

        .. py:property:: width()

            The width of this window.

    **Methods**

        .. py:method:: adjust_width(tot_width: int)

            Adjust width of this window.

        .. py:method:: describe(level=0)

            Generate a description as a sequence of lines.
