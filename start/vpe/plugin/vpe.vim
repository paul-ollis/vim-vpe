"
" Startup for the Vim Python Extensions.
"

if exists('g:loaded_vpe')
  finish
endif
let g:loaded_vpe = 1

command! VPERunThisAsPy call py3eval('VPE_run_this_as_py()')

py3 <<EOF
def _init_vpe_():
    """Initialise access to the VPE package.

    This is just a case of making sure that the correct directory is in sys.path.
    It will also source an optional post-initialisation script.
    """

    import pathlib
    import sys
    import vim as _vim

    this_dir = pathlib.Path(_vim.eval("expand('<sfile>')")).parent
    pack_dir = str(this_dir.parent.parent.parent)
    if pack_dir not in sys.path:
       sys.path.append(pack_dir)

    # If the user has set g:vpe_post_load_initrc then try to source it as a
    # vim script.
    if 'vpe_post_load_initrc' in _vim.vars:
        _vim.command(f'source {vim.vars["vpe_post_load_initrc"].decode()}')


def VPE_run_this_as_py():
    import importlib
    import pathlib

    import vim as _vim

    try:
        this_script = pathlib.Path(_vim.eval("expand('<sfile>')"))
        this_dir = pathlib.Path(_vim.eval("expand('<sfile>')")).parent
        mod_name = f'{this_script.parent.name}.{this_script.stem}'
        mod = importlib.import_module(mod_name)
        mod.run()
    except Exception as e:
        import traceback
        import io
        import vpe
        f = io.StringIO()
        traceback.print_exc(file=f)
        vpe.log(f.getvalue())
    return ''


_init_vpe_()
del _init_vpe_
EOF
