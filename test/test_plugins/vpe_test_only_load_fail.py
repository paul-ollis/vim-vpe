"""VPE-plugin: A plug-in that fails to load due to an exception."""

from vpe import vim

vim.vars.vpe_plugin_load_fail_err = 1
assert 0

vim.vars.vpe_plugin_load_fail_err += 1
