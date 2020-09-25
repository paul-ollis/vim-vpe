#!/usr/bin/env python
"""All the tests."""

import os
import sys

sys.path[0:0] = [os.path.abspath('..')]

import CleverSheep
print(CleverSheep.__file__)
from CleverSheep.Test.Tester import runTree

if __name__ == '__main__':
    runTree()
