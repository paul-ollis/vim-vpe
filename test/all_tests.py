#!/usr/bin/env python
"""All the tests."""

import os
import sys

sys.path[0:0] = [os.path.abspath('..')]

import cleversheep3
print(cleversheep3.__file__)
from cleversheep3.Test.Tester import runTree

if __name__ == '__main__':
    runTree()
