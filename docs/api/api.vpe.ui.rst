Module vpe.ui
=============


.. py:module:: ui

User interface components.

This is still being developed. The API and behaviour is likely to change.

.. rubric:: BoolField

.. py:class:: BoolField(...)

    .. code::

        BoolField(
                lidx,
                cidx,
                prefix='',
                suffix='',
                prefix_width=0,
                suffix_width=0,
                value_width=6,
                opt_var=None,

    A field displaying a boolean value.

    **Methods**

        .. py:method:: increment(_step: int) -> bool

            Increment this field's value by a given step.

.. rubric:: ChoiceField

.. py:class:: ChoiceField(_values=(),opt_var=None,**kwargs)

    A field holding one of a list of choices.

    ::values: A sequence of permitted values for the field. This is ignored.

    **Methods**

        .. py:method:: increment(step: int)

            Increment this field's value by a given step.

.. rubric:: ConfigPanel

.. py:class:: ConfigPanel(fields)

    A panel that displays configuration values.


    **Parameters**

    .. container:: parameters itemdetails

        *fields*
            The fields within this panel. A mapping from name to `Field`.


    **Attributes**

        .. py:attribute:: fields

            The fields within this panel. A mapping from name to `Field`.


        .. py:attribute:: first_field_idx

            The global index of the first field in this panel.

        .. py:attribute:: selectable_fields

            A mapping from global field index to `Field` instance.

    **Methods**

        .. py:method:: apply_syntax()

            Apply syntax highlighting for this panel.

            This is only called when the panel's `start_lidx` is correctly set.

        .. py:method:: get_field_by_idx(index: int)

            Get the editable field with a given index.

        .. py:method:: index_fields(start_idx: int)

            Set up the mapping from field index to field.

        .. py:method:: on_format_contents()

            Refresh to formatted lines for this panel.

        .. py:method:: select_field(index: int)

            Select a specific field.

.. rubric:: ConfigPanelBuffer

.. py:class:: ConfigPanelBuffer(*args,**kwargs)

    A `PanelViewBuffer` that supports configuration panels.

    This tracks instances of `ConfigPanel` and sets up key mappings to navigate
    and modify the fields within them.

    **Methods**

        .. py:method:: config_panels() -> Iterator[ConfigPanel]

            Interate over all the configuration panels.

        .. py:method:: edit_field()

            Allow the user to edit the value of a field.

        .. py:method:: get_field_by_idx(index: int)

            Get the editable field with a given index.

        .. py:method:: inc_field(step: int)

            Increment the value in a field.


            **Parameters**

            .. container:: parameters itemdetails

                *step*: int
                    Value to change the field by. May be a negative value.

        .. py:method:: move_field(step: int = 0)

            Move to a different field.


            **Parameters**

            .. container:: parameters itemdetails

                *step*: int
                    Increment for the field index.

        .. py:method:: on_change()

            Perform common processing when value is changed.

            This is intended to be over-ridden by subclasses.

        .. py:method:: on_reindex()

            Perform special processing when line reindexing has occurred.

        .. py:method:: on_selected_field_change()

            Perform common processing when the selected field is changed.

            This is intended to be over-ridden by subclasses.

        .. py:method:: on_updates_applied(changes_occurred: bool)

            Perform special processing when buffer has been refreshed.

            When this is invoked, this buffer may not be in the active window
            and my even be hidden.

.. rubric:: CurPrev

.. py:class:: CurPrev(value)

    An value that knows its previous value.

    **Properties**

        .. py:property:: changed() -> bool

            Whether this value has been changed.

        .. py:property:: value()

            The current value.

    **Methods**

        .. py:method:: restore_prev()

            Restore this to its previous value..

.. rubric:: Field

.. py:class:: Field(...)

    .. code::

        Field(
                lidx,
                cidx,
                prefix='',
                suffix='',
                prefix_width=0,
                suffix_width=0,
                value_width=6,
                opt_var=None,

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

        .. py:attribute:: cidx

            The column index within the panel.

        .. py:attribute:: lidx

            The line index within the panel.

        .. py:attribute:: prefix

            The label displayed before the field.

        .. py:attribute:: prefix_width

            The width spec for the prefix. If not provided then this
            defaults to the width of the prefix + 1. If set to a
            negative number, the prefix is right justified.

        .. py:attribute:: suffix

            The label displayed after the field.

        .. py:attribute:: suffix_width

            The width spec for the prefix. It follows the same pattern
            as the prefix_width.

    **Properties**

        .. py:property:: column_range() -> Tuple[int, int]

            The range of columns occupied by this field.

        .. py:property:: full_width() -> int

            The full width occupied by this field.

        .. py:property:: prefix_fmt_width() -> int

            The width of this field's formatted prefix.

        .. py:property:: suffix_fmt_width() -> int

            The width of this field's formatted suffix.

        .. py:property:: val_extent() -> Tuple[int, int]

            The extent of this field's value.

            :return: A tuple of cnum, width.

        .. py:property:: value() -> Any

            The field's current value.

        .. py:property:: value_fmt_width() -> int

            The width of this field's formatted value.

        .. py:property:: value_str()

            Format the value as a string.

        .. py:property:: value_width() -> int

            The width used to display the field's value.

    **Methods**

        .. py:method:: edit_value() -> bool

            Allow the user to edit the value of a field.

            This typically needs to be over-ridden by subclasses.

            **Return value**

            .. container:: returnvalue itemdetails

                True if the value was modified.

        .. py:method:: increment(_step: int) -> bool

            Increment this field's value by a given step.

            This typically needs to be over-ridden by subclasses.

            **Return value**

            .. container:: returnvalue itemdetails

                True if the value was modified.

        .. py:method:: text() -> str

            Format the full text of the field.

.. rubric:: FieldVar

.. py:class:: FieldVar(_var)

    A value that is displayed by a Field.

    This class defines the protocol that a `Field` uses to access its
    underlying value.

    **Properties**

        .. py:property:: value()

            "The current value for this variable.

    **Methods**

        .. py:method:: __init__(_var)

            Initialisation.

        .. py:method:: set(_value: Any) -> str

            Try to set this option's value.


            **Return value**

            .. container:: returnvalue itemdetails

                A string describing why the attempt failed. An empty string
                if the value was set. This basic wrapper always returns an
                empty string.

        .. py:method:: values() -> List[Any]

            Return a set of the valid values for this field.


            **Return value**

            .. container:: returnvalue itemdetails

                A list of the valid values. An empty list means that this
                field's range of values is not defined using a set.

.. rubric:: IntField

.. py:class:: IntField(...)

    .. code::

        IntField(
                lidx,
                cidx,
                prefix='',
                suffix='',
                prefix_width=0,
                suffix_width=0,
                value_width=6,
                opt_var=None,

    A field displaying an integer value.

    **Methods**

        .. py:method:: edit_value() -> bool

            Allow the user to edit the value of a field.


            **Return value**

            .. container:: returnvalue itemdetails

                True if the value was modified.

.. rubric:: format_str

.. py:function:: format_str(s: str,width: int) -> str

    Format a string within a given field width.

    The string is truncated (if necessary) to the *width* and then left or
    right justified within the *width*. A *width* of zero results in an empty
    string.

    **Parameters**

    .. container:: parameters itemdetails

        *s*: str
            The string to justify.
        *width*: int
            The field width. Positive values mean left justified, negative mean
            right justified.
