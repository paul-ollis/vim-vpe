"""Types involved in tracking changes."""
from __future__ import annotations

import warnings

from collections.abc import Iterator, MutableSequence

from typing import ClassVar

# TODO: Consider converting 'insert-above' cases to AddBelow.


class Operation:
    """Base for each type of a line buffer modification.

    This stores information about changes to a sub-sequence of lines. This
    stores information about what has changed, not the details of the change.
    For example, it will identify that N lines have been added after a given
    line, but not the contents of those new lines.

    This is not directly instantiated by VPE code, one of the subclasses
    `AddOp`, `DeleteOp` or `ChangeOp` is always used. And these should be
    created using the `from_vim_change` class method.

    :lnum:  The ``lnum`` value from a Vim change list entry.
    :end:   The ``end`` value from a Vim change list entry.
    :added: The ``added`` value from a Vim change list entry.
    :col:   The ``col`` value from a Vim change list entry.

    @name:  The start of the affected line range == lnum - 1.
    @a:     The start of the affected line range == lnum - 1.
    @b:     The end of the affected line range  == end - 1.
    @delta: The change in line count, set from added.
    @col:   The first affected column == col - 1. This is a value the Vim
            supplies buffer listener callbacks. It is stored here but not used
            by any methods.
    """
    name: ClassVar[str] = ''

    def __init__(self, lnum: int, end: int, added: int, col:int):
        self.a = lnum - 1
        self.b = end - 1
        self.delta = added
        self.col = col - 1

    @property
    def count(self) -> int:
        """The number of lines affected.

        This is always zero or more, zero indicating a change operation.
        """
        return abs(self.delta)

    @classmethod
    def create(
            cls, lnum: int, end: int, added: int, col: int = 1) -> Operation:
        """Create the appropriate Operation subclass.

        :lnum:  The starting line number for the operation.
        :end:   The ending line number (exclusive) for the operation.
        :added: How many lines were added. A negative value indicates that
                lines were deleted. A value of zero indicates that the lines
                were changed.
        :col:   The starting column for a change.
        """
        if added == 0:
            return ChangeOp(lnum, end, added, col)
        elif added > 0:
            return AddOp(lnum, end, added, col)
        else:
            return DeleteOp(lnum, end, added, col)

    def apply_to(self, buf: MutableSequence[str]):
        """Simplistically apply this change to a line buffer.

        NOTE: This method may be removed because its usefulness is *very*
              questionable.

        This adds blank lines, delete lines or replaces lines with empty
        strings, depending on the specific Operation subclass.

        This is necessarily a simplistic operation because the `Operation`
        class does not store contents of added or changed lines.
        """

    def __getitem__(self, key):                              # pragma: no cover
        """Emulation of Vim's buffer modification operation dictionary.

        This is provided to avoid breaking the VPE 0.6 API too much, but using
        this is deprecated.
        """
        warnings.warn(
            f'Dictionary access to {self.__class__.__name__} is deprecated'
            ' and is scheduled for removal in version 1.0.'
            '\nUse attributes a, b, count and col instead.',
            category=DeprecationWarning)
        if key == 'lnum':
            return self.a + 1
        elif key == 'end':
            return self.b + 1
        elif key == 'added':
            return self.count
        elif key == 'col':
            return self.col + 1
        else:
            raise KeyError(key)

    def items(self) -> Iterator[tuple[str, int]]:            # pragma: no cover
        """Emulation of Vim's buffer modification operation dictionary.

        This is provided to avoid breaking the VPE 0.6 API too much, but using
        this is deprecated.
        """
        # pylint: disable=unnecessary-dunder-call
        warnings.warn(
            f'Dictionary access to {self.__class__.__name__} is deprecated'
            ' and is scheduled for removal in version 0.9.'
            '\nUse attributes a, b, count and col instead.',
            DeprecationWarning)
        for key in ('lnum', 'end', 'added', 'col'):
            yield key, self.__getitem__(key)

    def __eq__(self, other: Operation):
        return (
            self.a == other.a and self.b == other.b
            and self.delta == other.delta and self.col == other.col)

    def __repr__(self):
        name = self.__class__.__name__
        return f'<{name}:{self.a}.{self.col}-{self.b},{self.count}>'

    # Deprecated method names for backward compatability.
    from_vim_change = create


class AddOp(Operation):
    """A buffer addition operation."""
    name: ClassVar[str] = 'add'


class DeleteOp(Operation):
    """A buffer deletion operation."""
    name: ClassVar[str] = 'delete'


class ChangeOp(Operation):
    """A buffer change operation."""
    name: ClassVar[str] = 'change'

    def __repr__(self):
        name = self.__class__.__name__
        return f'<{name}:{self.a}.{self.col}-{self.b}>'
