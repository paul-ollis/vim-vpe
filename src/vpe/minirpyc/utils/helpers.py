"""Helpers and wrappers for common RPyC tasks."""

from ..lib.colls import WeakValueDict
from ..core.consts import HANDLE_BUFFITER, HANDLE_CALL
from ..core.netref import syncreq


def buffiter(obj, chunk=10, max_chunk=1000, factor=2):
    """Buffered iterator - reads the remote iterator in chunks starting with
    *chunk*, multiplying the chunk size by *factor* every time, as an
    exponential-backoff, up to a chunk of *max_chunk* size.

    ``buffiter`` is very useful for tight loops, where you fetch an element
    from the other side with every iterator. Instead of being limited by the
    network's latency after every iteration, ``buffiter`` fetches a "chunk"
    of elements every time, reducing the amount of network I/Os.

    :param obj: An iterable object (supports ``iter()``)
    :param chunk: the initial chunk size
    :param max_chunk: the maximal chunk size
    :param factor: the factor by which to multiply the chunk size after every
                   iterator (up to *max_chunk*). Must be >= 1.

    :returns: an iterator

    Example::

        cursor = db.get_cursor()
        for id, name, dob in buffiter(cursor.select("Id", "Name", "DoB")):
            print id, name, dob
    """
    if factor < 1:
        raise ValueError("factor must be >= 1, got %r" % (factor,))
    it = iter(obj)
    count = chunk
    while True:
        items = syncreq(it, HANDLE_BUFFITER, count)
        count = min(count * factor, max_chunk)
        if not items:
            break
        for elem in items:
            yield elem
