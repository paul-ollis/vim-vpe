Module vpe.ui
=============

.. py:module:: vpe.ui

User interface components.

This is still being developed. The API and behaviour is likely to change.

BoolField
---------

.. py:class:: vpe.ui.BoolField(...)

    .. parsed-literal::

        BoolField(
            \*,
            lidx,
            cidx,
            prefix='',
            suffix='',
            prefix_width=0,
            suffix_width=0,
            value_width=6,
            opt_var=None,
            \*\*kwargs)

    A field displaying a boolean value.

    **Methods**

        .. py:method:: vpe.ui.BoolField.increment(_step: int) -> bool

            Increment this field's value by a given step.

ChoiceField
-----------

.. py:class:: vpe.ui.ChoiceField(values=(),opt_var=None,**kwargs)

    A field holding one of a list of choices.


    **Parameters**

    .. container:: parameters itemdetails

        *values*
            A sequence of permitted values for the field.

    **Attributes**

        .. py:attribute:: vpe.ui.ChoiceField.values

            A sequence of permitted values for the field.

    **Methods**

        .. py:method:: vpe.ui.ChoiceField.increment(step: int)

            Increment this field's value by a given step.

ConfigPanel
-----------

.. py:class:: vpe.ui.ConfigPanel(fields)

    A panel that displays configuration values.


    **Parameters**

    .. container:: parameters itemdetails

        *fields*
            The fields within this panel. A mapping from name to `Field`.


    **Attributes**

        .. py:attribute:: vpe.ui.ConfigPanel.fields

            The fields within this panel. A mapping from name to `Field`.


        .. py:attribute:: vpe.ui.ConfigPanel.first_field_idx

            The global index of the first field in this panel.

        .. py:attribute:: vpe.ui.ConfigPanel.selectable_fields

            A mapping from global field index to `Field` instance.

    **Methods**

        .. py:method:: vpe.ui.ConfigPanel.apply_syntax()

            Apply syntax highlighting for this panel.

            This is only called when the panel's `start_lidx` is correctly set.

        .. py:method:: vpe.ui.ConfigPanel.get_field_by_idx(index: int)

            Get the editable field with a given index.

        .. py:method:: vpe.ui.ConfigPanel.index_fields(start_idx: int)

            Set up the mapping from field index to field.

        .. py:method:: vpe.ui.ConfigPanel.on_format_contents()

            Refresh to formatted lines for this panel.

        .. py:method:: vpe.ui.ConfigPanel.select_field(index: int)

            Select a specific field.

ConfigPanelBuffer
-----------------

.. py:class:: vpe.ui.ConfigPanelBuffer(*args,**kwargs)

    A `PanelViewBuffer` thats supports configuration panels.

    This tracks instances of `ConfigPanel` and sets up key mappings to navigate
    and modify the fields within them.

    **Methods**

        .. py:method:: vpe.ui.ConfigPanelBuffer.config_panels() -> Iterator[ConfigPanel]

            Interate over all the configuration panels.

        .. py:method:: vpe.ui.ConfigPanelBuffer.edit_field()

            Allow the user to edit the value of a field.

        .. py:method:: vpe.ui.ConfigPanelBuffer.get_field_by_idx(index: int)

            Get the editable field with a given index.

        .. py:method:: vpe.ui.ConfigPanelBuffer.inc_field(step: int)

            Increment the value in a field.


            **Parameters**

            .. container:: parameters itemdetails

                *step*: int
                    Value to change the field by. May be a negative value.

        .. py:method:: vpe.ui.ConfigPanelBuffer.move_field(step: int = 0)

            Move to a different field.


            **Parameters**

            .. container:: parameters itemdetails

                *step*: int
                    Increment for the field index.

        .. py:method:: vpe.ui.ConfigPanelBuffer.on_change()

            Perform common processing when value is changed.

            This is intended to be over-ridden by subclasses.

        .. py:method:: vpe.ui.ConfigPanelBuffer.on_reindex()

            Perform special processing when line reindexing has occurred.

        .. py:method:: vpe.ui.ConfigPanelBuffer.on_selected_field_change()

            Perform common processing when the selecetd field is changed.

            This is intended to be over-ridden by subclasses.

        .. py:method:: vpe.ui.ConfigPanelBuffer.on_updates_applied(changes_occurred: bool)

            Perform special processing when buffer has been refreshed.

            When this is invoked, this buffer may not be in the active window
            and my even be hidden.

CurPrev
-------

.. py:class:: vpe.ui.CurPrev(value)

    An value that knows its previous value.

Field
-----

.. py:class:: vpe.ui.Field(...)

    .. parsed-literal::

        Field(
            \*,
            lidx,
            cidx,
            prefix='',
            suffix='',
            prefix_width=0,
            suffix_width=0,
            value_width=6,
            opt_var=None,
            \*\*kwargs)

    Base class for a field within a `ConfigPanel`.

    A field consists of 3 parts; prefix, value and suffix. They are laid out
    like this (in this example the prefix and value are left justified and the
    suffix is right justified).

    ::

      |        prefix      value          suffix
      |        :          ::        ::         :
      |        :          ::        :<--------->  suffix_fmt_width
      |        <---------->:        :          :  prefix_fmt_width
      |        :           <-------->          :  val_extent[1] / value_width
      |        <------------------------------->  full_width
       ^       ^           ^
       :       :           `--------------------  val_extent[0]
       :       `--------------------------------  cidx
       `----------------------------------------  <buffer column zero>

    Note that full_width == prefix_fmt_width + value_width + suffix_fmt_width.

    **Parameters**

    .. container:: parameters itemdetails

        *lidx*
            The line index within the panel.
        *cidx*
            The column index within the panel.
        *prefix*
            The label displayed before the field.
        *suffix*
            The label displayed after the field.
        *prefix_width*
            The width spec for the prefix. If not provided then this
            defaults to the width of the prefix + 1. If set to a
            negative number, the prefix is right justified.
        *suffix_width*
            The width spec for the prefix. It follows the same pattern
            as the prefix_width.
        *value_width*
            The width spec for the value. It follows the same pattern
            as the prefix_width.

    **Attributes**

        .. py:attribute:: vpe.ui.Field.cidx

            The column index within the panel.

        .. py:attribute:: vpe.ui.Field.lidx

            The line index within the panel.

        .. py:attribute:: vpe.ui.Field.prefix

            The label displayed before the field.

        .. py:attribute:: vpe.ui.Field.prefix_width

            The width spec for the prefix. If not provided then this
            defaults to the width of the prefix + 1. If set to a
            negative number, the prefix is right justified.

        .. py:attribute:: vpe.ui.Field.suffix

            The label displayed after the field.

        .. py:attribute:: vpe.ui.Field.suffix_width

            The width spec for the prefix. It follows the same pattern
            as the prefix_width.

    **Properties**

        .. py:method:: vpe.ui.Field.column_range() -> Tuple[int, int]
            :property:

            The range of columns occupied by this field.

        .. py:method:: vpe.ui.Field.full_width() -> int
            :property:

            The full width occupied by this field.

        .. py:method:: vpe.ui.Field.prefix_fmt_width() -> int
            :property:

            The width of this field's formatted prefix.

        .. py:method:: vpe.ui.Field.suffix_fmt_width() -> int
            :property:

            The width of this field's formatted suffix.

        .. py:method:: vpe.ui.Field.val_extent() -> Tuple[int, int]
            :property:

            The extent of this field's value.

            :return: A tuple of cnum, width.

        .. py:method:: vpe.ui.Field.value() -> typing.Any
            :property:

            The field's current value.

        .. py:method:: vpe.ui.Field.value_fmt_width() -> int
            :property:

            The width of this field's formatted value.

        .. py:method:: vpe.ui.Field.value_str()
            :property:

            Format the value as a string.

        .. py:method:: vpe.ui.Field.value_width() -> int
            :property:

            The width used to display the field's value.

    **Methods**

        .. py:method:: vpe.ui.Field.text() -> str

            Format the full text of the field.

    **Static methods**

        .. py:staticmethod:: vpe.ui.Field.edit_value() -> bool

            Allow the user to edit the value of a field.

            This typically needs to be over-ridden by subclasses.

            **Return value**

            .. container:: returnvalue itemdetails

                True if the value was modified.

        .. py:staticmethod:: vpe.ui.Field.increment(_step: int) -> bool

            Increment this field's value by a given step.

            This typically needs to be over-ridden by subclasses.

            **Return value**

            .. container:: returnvalue itemdetails

                True if the value was modified.

FieldVar
--------

.. py:class:: vpe.ui.FieldVar(_var)

    A value that is displayed by a Field.

    This class defines the protocol that a `Field` uses to access its
    underlying value.

    **Properties**

        .. py:method:: vpe.ui.FieldVar.value()
            :property:

            "The current value for this variable.

    **Methods**

        .. py:method:: vpe.ui.FieldVar.__init__(_var)

            Initialisation.

        .. py:method:: vpe.ui.FieldVar.set(value: typing.Any) -> str

            Try to set this option's value.


            **Return value**

            .. container:: returnvalue itemdetails

                A string describing why the attempt failed. An empty string
                if the value was set. This basic wrapper always returns an
                empty string.

        .. py:method:: vpe.ui.FieldVar.values() -> List[typing.Any]

            Return a set of the valid values for this field.


            **Return value**

            .. container:: returnvalue itemdetails

                A list of the valid values. An empty list means that this
                field's range of values is not defined using a set.

IntField
--------

.. py:class:: vpe.ui.IntField(...)

    .. parsed-literal::

        IntField(
            \*,
            lidx,
            cidx,
            prefix='',
            suffix='',
            prefix_width=0,
            suffix_width=0,
            value_width=6,
            opt_var=None,
            \*\*kwargs)

    A field displaying an integer value.

    **Methods**

        .. py:method:: vpe.ui.IntField.edit_value() -> bool

            Allow the user to edit the value of a field.


            **Return value**

            .. container:: returnvalue itemdetails

                True if the value was modified.

format_str
----------

.. py:function:: vpe.ui.format_str(s: str,width: int) -> str

    Format a string within a given field width.

    The string is truncated (if necessary) to the *width* and then left or
    right justified within the *width*. A *width* of zero results in an empty
    string.

    **Parameters**

    .. container:: parameters itemdetails

        *s*: str
            The string to justify.
        *width*: int
            The field width. Postive values mean left justified, negative mean
            right justified.