.. IMPORTANT: This is an auto-generated file.

Module vpe.diffs
================


.. py:module:: diffs

Types involved in tracking changes.

.. rubric:: AddOp

.. py:class:: AddOp(lnum: int, end: int, added: int, col: int)

    A buffer addition operation.

.. rubric:: ChangeOp

.. py:class:: ChangeOp(lnum: int, end: int, added: int, col: int)

    A buffer change operation.

.. rubric:: DeleteOp

.. py:class:: DeleteOp(lnum: int, end: int, added: int, col: int)

    A buffer deletion operation.

.. rubric:: Operation

.. py:class:: Operation(lnum: int, end: int, added: int, col: int)

    Base for each type of a line buffer modification.

    This stores information about changes to a sub-sequence of lines. This
    stores information about what has changed, not the details of the change.
    For example, it will identify that N lines have been added after a given
    line, but not the contents of those new lines.

    This is not directly instantiated by VPE code, one of the subclasses
    `AddOp`, `DeleteOp` or `ChangeOp` is always used. And these should be
    created using the `from_vim_change` class method.

    **Parameters**

    .. container:: parameters itemdetails

        *lnum*
            The ``lnum`` value from a Vim change list entry.
        *end*
            The ``end`` value from a Vim change list entry.
        *added*
            The ``added`` value from a Vim change list entry.
        *col*
            The ``col`` value from a Vim change list entry.


    **Attributes**

        .. py:attribute:: a

            The start of the affected line range == lnum - 1.

        .. py:attribute:: b

            The end of the affected line range  == end - 1.

        .. py:attribute:: col

            The first affected column == col - 1. This is a value the Vim
            supplies buffer listener callbacks. It is stored here but not used
            by any methods.

        .. py:attribute:: delta

            The change in line count, set from added.

        .. py:attribute:: name
            :type: ClassVar:

            The start of the affected line range == lnum - 1.

    **Properties**

        .. py:property:: count() -> int

            The number of lines affected.

            This is always zero or more, zero indicating a change operation.

    **Methods**

        .. py:method:: __getitem__(key)

            Emulation of Vim's buffer modification operation dictionary.

            This is provided to avoid breaking the VPE 0.6 API too much, but using
            this is deprecated.

        .. py:method:: apply_to(buf: MutableSequence[str])

            Simplistically apply this change to a line buffer.

            NOTE: This method may be removed because its usefulness is *very*
                  questionable.

            This adds blank lines, delete lines or replaces lines with empty
            strings, depending on the specific Operation subclass.

            This is necessarily a simplistic operation because the `Operation`
            class does not store contents of added or changed lines.

        .. py:method:: items() -> Iterator[tuple[str, int]]

            Emulation of Vim's buffer modification operation dictionary.

            This is provided to avoid breaking the VPE 0.6 API too much, but using
            this is deprecated.

    **Class methods**

        .. py:classmethod:: create(...)

            .. code::

                create(
                        lnum: int,
                        end: int,
                        added: int,
                        col: int = 1

            Create the appropriate Operation subclass.


            **Parameters**

            .. container:: parameters itemdetails

                *lnum*: int
                    The starting line number for the operation.
                *end*: int
                    The ending line number (exclusive) for the operation.
                *added*: int
                    How many lines were added. A negative value indicates that
                    lines were deleted. A value of zero indicates that the lines
                    were changed.
                *col*: int
                    The starting column for a change.

        .. py:classmethod:: from_vim_change(...)

            .. code::

                from_vim_change(
                        lnum: int,
                        end: int,
                        added: int,
                        col: int = 1

            Create the appropriate Operation subclass.


            **Parameters**

            .. container:: parameters itemdetails

                *lnum*: int
                    The starting line number for the operation.
                *end*: int
                    The ending line number (exclusive) for the operation.
                *added*: int
                    How many lines were added. A negative value indicates that
                    lines were deleted. A value of zero indicates that the lines
                    were changed.
                *col*: int
                    The starting column for a change.