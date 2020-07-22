#!/usr/bin/env python
"""All the tests."""
__docformat__ = "restructuredtext"

import os

from CleverSheep.Test.Tester import *

import support


def init():
    vim = support.VimClient()
    vim.command(f'cd {os.getcwd()}')
    vim.command(f'source init.vim')


init()
runTree()
