"""A minimialist fork of RPyC.

Remote Python Call mini(RPyC)
Licensed under the MIT license (see `LICENSE` file)

This is a cut-down version of RPyC by Tomer Filiba, created to support remote
control of the Vim editor using Python.
"""

from .core import (
    BaseNetref, ClassicService, Connection,
    GenericException, MasterService, Service, SlaveService, VoidService)
from .utils.helpers import buffiter
