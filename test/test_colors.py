"""Tests for the VPE colour support."""

# pylint: disable=unused-wildcard-import,wildcard-import
# pylint: disable=deprecated-method
# pylint: disable=wrong-import-order

import os
import shutil
from pathlib import Path

from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import runModule, test

import support

from vpe import colors

_run_after = ['test_vim.py']


class ColoursTests(support.Base):
    """The colors module."""

    @test(testID='colours-well-defined')
    def well_defined_name(self):
        """Various name forms can be converted to a well defined form."""
        good_name = colors.well_defined_name('LightSeaGreen')
        failUnlessEqual('LightSeaGreen', good_name)

        good_name = colors.well_defined_name('light sea green')
        failUnlessEqual('LightSeaGreen', good_name)

        good_name = colors.well_defined_name('lightSeaGreen')
        failUnlessEqual('LightSeaGreen', good_name)

    @test(testID='colours-grey')
    def well_defined_name_grey(self):
        """Well defined names handle both spellings of grey."""
        good_name = colors.well_defined_name('LightSlateGrey')
        failUnlessEqual('LightSlateGrey', good_name)

        good_name = colors.well_defined_name('LightSlateGray')
        failUnlessEqual('LightSlateGray', good_name)

    @test(testID='colours-terminal')
    def colour_terminal_colour_match(self):
        """A colour can be matched to a 256 colour terminal colour name."""

        # LightSeaGreen is a 'standard' Xterm colour, which converts simply.
        v = colors.to_256_num('LightSeaGreen')
        failUnlessEqual(37, v)

        # BlanchedAlmond is not a standard Xterm colour, so conversion requires
        # first mapping to a similar colour.
        v = colors.to_256_num('BlanchedAlmond')
        failUnlessEqual(224, v)
