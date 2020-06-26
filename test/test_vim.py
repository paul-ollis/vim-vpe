"""The core VPE tests."""

import functools
import os
import pathlib
import subprocess
import time

from CleverSheep.Test import Tester
from CleverSheep.Test.Tester import *

import support


class Base(Suite):
    """Base for Vim tests."""

    def do_checks(self):
        i = None
        for i, result in enumerate(support.get_test_results(
                f'data-out/{self.name}.txt', Tester.currentTest().testID)):
            support.check_result(result)
        failIf(i is None, f'No results for {Tester.currentTest().testID}')

        msg_path = f'data-out/{self.name}.txt.msg'
        with open(msg_path) as f:
            text = f.read()
        if text.strip():
            support.cons(text.rstrip())
            fail(f'Messages were produced, see {msg_path}')

    def suiteSetUp(self):
        sentinel = pathlib.Path('data-out/sentinel')
        vim = self.vim = support.VimClient()
        with open(f'data-out/{self.name}.txt', 'w'):
            pass
        vim.command(f'cd {os.getcwd()}')
        vim.command(f'source init.vim')
        msg_path = f'data-out/{self.name}.txt.msg'
        sentinel.unlink(missing_ok=True)
        vim.command(f'py3file vim-scripts/{self.name}.py')

        when = time.time() + 1.0
        while not sentinel.exists() and time.time() < when:
            time.sleep(0.01)
        vim.sync()

    def suiteTearDown(self):
        pass


class VimSuite(Base):
    """Basic behaviour of the Vim object."""
    name = 'basic_vim'

    @test(testID='vim-attr-types')
    def vim_attr_types(self):
        """Verify that Vim returns attributes of the correct type."""
        self.do_checks()

    @test(testID='comma-separated-flag-option')
    def comma_separated_flags_options(self):
        """Verify that comma separated flag options work correctly."""
        self.do_checks()

    @test(testID='flag-option')
    def flag_options(self):
        """Verify that flag options work correctly."""
        self.do_checks()

    @test(testID='list-option')
    def list_options(self):
        """Verify that list options work correctly."""
        self.do_checks()

    @test(testID='global-option')
    def global_options(self):
        """Verify that global options work correctly."""
        self.do_checks()

    @test(testID='vim-read-only-attrs')
    def read_only_attrs(self):
        """The Vim class enforces read-only attributes."""
        self.do_checks()

    @test(testID='mod-overrides-functions')
    def mod_overrides_function(self):
        """Vim module attributes are used in preference to Vim functions."""
        self.do_checks()

    @test(testID='current')
    def current(self):
        """The Vim current attributes provides wrapped attributes."""
        self.do_checks()

    @test(testID='vim-singletons')
    def vim_singletons(self):
        """Verify that certain Vim attributes are singletons."""
        self.do_checks()


class BuffersSuite(Base):
    """Basic behaviour of the Buffers object."""
    name = 'basic_buffers'

    @test(testID='buffers-attr-types')
    def vim_attr_types(self):
        """Verify that Vim returns attributes of the correct type."""
        self.do_checks()


class BufferSuite(Base):
    """Basic behaviour of the Buffer object."""
    name = 'basic_buffer'

    @test(testID='buffer-attr-types')
    def buf_attr_types(self):
        """Verify that a vpe.Buffer returns attributes of the correct type."""
        self.do_checks()

    @test(testID='buffer-append')
    def buf_append(self):
        """Verify that buffers can be appended to."""
        self.do_checks()

    @test(testID='buffer-marks')
    def buffer_marks(self):
        """Verify that buffers marks work."""
        self.do_checks()


class RangeSuite(Base):
    """Basic behaviour of the Range object."""
    name = 'basic_range'

    @test(testID='range-attr-types')
    def buf_attr_types(self):
        """Verify that a vpe.Buffer returns attributes of the correct type."""
        self.do_checks()

    @test(testID='range-append')
    def buf_append(self):
        """Verify that buffers can be appended to."""
        self.do_checks()


class WindowsSuite(Base):
    """Basic behaviour of the Windows object."""
    name = 'basic_windows'

    @test(testID='windows-attr-types')
    def vim_attr_types(self):
        """Verify that Window returns attributes of the correct type."""
        self.do_checks()


class WindowSuite(Base):
    """Basic behaviour of the Window object."""
    name = 'basic_window'

    @test(testID='window-attr-types')
    def attr_types(self):
        """Verify that a vpe.Window returns attributes of the correct type."""
        self.do_checks()

    @test(testID='window-writeable-attrs')
    def writeable_attrs(self):
        """Verify that some window attributes are writeable."""
        self.do_checks()


class TabPagesSuite(Base):
    """Basic behaviour of the TabPages object."""
    name = 'basic_tabpages'

    @test(testID='tabpages-attr-types')
    def vim_attr_types(self):
        """Verify that TabPage returns attributes of the correct type."""
        self.do_checks()


class TabPageSuite(Base):
    """Basic behaviour of the TabPage object."""
    name = 'basic_tabpage'

    @test(testID='tabpage-attr-types')
    def attr_types(self):
        """Verify that a vpe.TabPage returns attributes of the correct type."""
        self.do_checks()


runModule()
