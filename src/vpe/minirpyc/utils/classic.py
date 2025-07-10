# pylint: disable=too-many-arguments
# pylint: disable=redefined-builtin
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

import inspect
import os
import pickle
import sys
from contextlib import contextmanager

from ..core.consts import STREAM_CHUNK
from ..core.service import ClassicService, ModuleNamespace, Slave


DEFAULT_SERVER_PORT = 18812
DEFAULT_SERVER_SSL_PORT = 18821

SlaveService = ClassicService   # avoid renaming SlaveService in this module for now

# ===============================================================================
# remoting utilities
# ===============================================================================


def interact(conn, namespace=None):
    """remote interactive interpreter

    :param conn: the RPyC connection
    :param namespace: the namespace to use (a ``dict``)
    """
    if namespace is None:
        namespace = {}
    namespace["conn"] = conn
    with redirected_stdio(conn):
        conn.execute("""def _rinteract(ns):
            import code
            code.interact(local = dict(ns))""")
        conn.namespace["_rinteract"](namespace)


class MockClassicConnection(object):
    """Mock classic RPyC connection object. Useful when you want the same code to run remotely or locally.
    """

    def __init__(self):
        self.root = Slave()
        ClassicService._install(self, self.root)
