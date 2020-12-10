"""VPE-plugin: A plug-in that aborts loading.

The vpe.Finish exception is used for this.
"""

import vpe
from vpe import vim

vim.vars.vpe_plugin_load_abort = 1
raise vpe.Finish('Abort for VPE testing.')

vim.vars.vpe_plugin_load_abort += 1
