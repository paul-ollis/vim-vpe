"""VPE's own plug-in support mechanism."""
# pylint: disable=deprecated-method

import os
import platform
import shutil
import time
from pathlib import Path

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import runModule, test

import support

import vpe

_run_after = ['test_vim.py', 'test_mapping_x.py']


def install_test_plugins(dot_vim_dir: str):
    """Install special test plug-in code."""
    plugin_dir_path = Path(dot_vim_dir) / 'pack' / 'vpe_plugins'
    test_plugin_path = Path(__file__).parent / 'test_plugins'

    init = plugin_dir_path / '__init__.py'
    plugin_dir_path.mkdir(parents=True, exist_ok=True)
    added_files = set()
    added_dirs = set()
    for path in test_plugin_path.glob('**/*.py'):
        rel_path = path.relative_to(test_plugin_path)
        dest = plugin_dir_path / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        added_files.add(dest)
        if rel_path.parent != Path('.'):
            added_dirs.add(plugin_dir_path / rel_path.parent)
        plugin_dir_path.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)

    # Remove the __init__.py file so we test that VPE creates it if required.
    if init.exists():
        os.unlink(str(init))

    return init, added_dirs, added_files


class TestPlugin(support.Base):
    """Core VPE plug-in behaviour."""

    def suiteSetUp(self):
        """Make sure Vim gets restarted with test plug-ins in place.

        :<py>:
            res = Struct()
            res.dot_vim_dir = vpe.dot_vim_dir()
            dump(res)
        """
        super().suiteSetUp()
        res = self.run_suite_setup()
        self.stop_vim_session()
        self.init_py, *self.added_paths = install_test_plugins(res.dot_vim_dir)
        super().suiteSetUp()

    def suiteTearDown(self):
        """Clean up added plug-in files."""
        super().suiteSetUp()
        added_dirs, added_files = self.added_paths
        for p in added_files:
            try:
                p.unlink()
            except OSError:
                pass
        for p in added_dirs:
            shutil.rmtree(p, ignore_errors=True)

    @test(testID='plugin-load-ok')
    def load(self):
        """VPE automatically loads plug-ins.

        :<py>:
            res = Struct()
            res.ok_plugin = vim.vars.vpe_plugin_load_ok
            res.ok_plugin_package = vim.vars.vpe_plugin_package_load_ok
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.ok_plugin)

    @test(testID='plugin-fail-err')
    def load_err_fail(self):
        """VPE handles plug-ins that fail to load due an error.

        :<py>:
            res = Struct()
            res.plugin_err = vim.vars.vpe_plugin_load_fail_err
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.plugin_err)

    @test(testID='plugin-load-abort')
    def load_abort(self):
        """A plug-in can abort loading using th Finish exception.

        :<py>:
            res = Struct()
            res.plugin_abort = vim.vars.vpe_plugin_load_abort
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.plugin_abort)

    @test(testID='plugin-skip-non-plugin')
    def ignore_non_plugin(self):
        """VPE ignores Python files that are not plug-ins.

        :<py>:
            res = Struct()
            res.invalid = vim.vars.vpe_plugin_invalid
            res.invalid_package = vim.vars.vpe_plugin_package_invalid
            res.invalid_non_package = vim.vars.vpe_just_a_file_invalid
            dump(res)
        """
        res = self.run_self()
        failUnless(res.invalid is None)
        failUnless(res.invalid_package is None)
        failUnless(res.invalid_non_package is None)

    @test(testID='plugin-init-created')
    def init_created(self):
        """VPE creates __init__.py in the plug-in directory, as required.

        :<py>:
            res = Struct()
            res.plugin_err = vim.vars.vpe_plugin_load_fail_err
            dump(res)
        """
        res = self.run_self()
        failUnless(time.time() - self.init_py.stat().st_mtime < 10.0)

    @test(testID='plugin-load-hook')
    def load_hook(self):
        """The user can add hook functions to be invoked upon plugin init.

        :<py>:
            res = Struct()
            res.plugin_hook_loaded = vim.vars.vpe_plugin_hook_loaded
            res.plugin_hook_ok = vim.vars.vpe_plugin_hook_ok
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.plugin_hook_loaded)
        failUnlessEqual(1, res.plugin_hook_ok)

    @test(testID='plugin-load-hook-err')
    def load_hook_error(self):
        """Errors in the hook callback are handled gracefully.

        :<py>:
            res = Struct()
            res.plugin_hook_loaded = vim.vars.vpe_plugin_hook_loaded
            res.plugin_hook_ok = vim.vars.vpe_plugin_hook_ok
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(1, res.plugin_hook_loaded)
        failUnlessEqual(1, res.plugin_hook_ok)


if __name__ == '__main__':
    runModule()
