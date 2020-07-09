"
" Startup for the Vim Pyth Extensions.
"


function! VPE_py_call(...)
    let g:VPE_py_args = a:000
    let g:VPE_ret = ''
py3 <<EOF
import vpe
vim = vpe.Vim()
vpe.dispatch(*vim.vars.VPE_py_args)
EOF
    return g:VPE_ret
endfunction


py3 <<EOF
def _init_vpe_():
    """Initialise access to the VPE package.

    This is just a case of making sure that the correct directory is in sys.path.
    It will also source an optional post-initialisation script.
    """

    import pathlib
    import sys

    import vim

    this_dir = pathlib.Path(vim.eval("expand('<sfile>')")).parent
    pack_dir = str(this_dir.parent.parent.parent)
    if pack_dir not in sys.path:
       sys.path.append(pack_dir)

    # " If the user has set g:vpe_post_load_initrc then try to source it as a vim
    # script.

    if 'vpe_post_load_initrc' in vim.vars:
        vim.command(f'source {vim.vars["vpe_post_load_initrc"].decode()}')


_init_vpe_()
del _init_vpe_
EOF
