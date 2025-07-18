"""Support for various type of resource.

The type in this module attempt to provide efficient sources for variouse
resources.
"""
from __future__ import annotations

import heapq


class IntIdentifierPool:
    """A source of unique integer IDs.

    This can be used for situations where Vim requires an integer ID to be
    supplied. We could just use an ``itertools.counter``, but that can
    technically produce values greater than MAXINT; unlikely in these 64-bit
    days, but 32-bit is still around.

    This saves freed IDs for preferential allocation. The smalest freed value
    is allocated first. Freed IDs are efficiently stored as 32-bit unsigned
    values.

    As new allocations are made, the next_new_id increments, but when IDs
    are freed the pool of free IDs is filled. The number line of IDs looks
    something like::

         MIN_ID
         v
         alloc   part freed                   alloc     next_new_id
        ,-----. ,------------------------. ,----------. v
         .....   nnnnnnnnnnn.nnn.nnnnnnnn   ..........  .

    IDs start from 10, which allows some small values to be used for special
    purposes by users of this class. This class attempts to minimise the space
    occupied by ``part freed``. The ``next_new_id`` will naturally limited by
    the total UIDs allocated. The wa that ``part freed`` is minimised is by
    reorganinising the above number line to::

         MIN_ID
         v
         alloc   reuse range     part freed     alloc       next_new_id
        ,-----. ,-----------. ,------------. ,----------. v
         .....   nnnnnnnnnnn   nnn.nnnnnnnn   ..........  .

    The reuse range can be stored as a simple (a, b) tuple oo range. The part free
    section is stored as a heapq, which allows freed value to be efficiently
    inserted. It also allows the reuse range to be efficently created and
    updated.

    Note that this class only stores the MIN_ID (const), 'reuse range', 'part
    freed' and 'next_new_id'.

    If your use-case results in 'part-freed' tending to be small then this
    class is a good choice.
    """

    MIN_ID = 10

    def __init__(self):
        self._next_new_id = self.MIN_ID
        self._reuse_range = range(self.MIN_ID, self.MIN_ID)
        self._free_pool = []

    def alloc(self):
        """Allocate an ID, preferentially using freed IDs."""
        if self._reuse_range:
            a, b = self._reuse_range.start,self._reuse_range.stop
            self._reuse_range = range(a + 1, b)
            return a
        elif not self._free_pool:
            v = self._next_new_id
            self._next_new_id += 1
            return v
        else:
            return heapq.heappop(self._free_pool)

    def free(self, uid: int):
        """Free an ID for re-use."""
        heapq.heappush(self._free_pool, uid)
        pool = self._free_pool
        r = self._reuse_range
        stop = r.stop
        while pool and pool[0] == stop:
            heapq.heappop(pool)
            stop += 1
        if stop > r.stop:
            self._reuse_range = range(r.start, stop)
