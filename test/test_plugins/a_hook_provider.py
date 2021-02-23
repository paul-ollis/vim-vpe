"""VPE-plugin: A plug-in to add a hook for another plug-in.

This is not very realistic, but is a pragmatic approach for testing.
"""

import vpe
from vpe import vim

vim.vars.vpe_plugin_hook_ok = 0


def my_test_hook():
    vim.vars.vpe_plugin_hook_ok += 1


def my_bad_test_hook():
    assert False, 'Oops'
    vim.vars.vpe_plugin_hook_ok += 1


vpe.add_post_plugin_hook('load_ok', my_test_hook)
vpe.add_post_plugin_hook('load_ok', my_bad_test_hook)
vpe.add_post_plugin_hook('no_such_plugin', my_test_hook)

vim.vars.vpe_plugin_hook_loaded = 1
