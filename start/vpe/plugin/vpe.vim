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

    This is primarily a case of making sure that the correct directory is in
    sys.path.
    """
    # Use imports within function to minimise global namespace polution.
    import pathlib
    import sys
    import vim as _vim

    this_dir = pathlib.Path(_vim.eval("expand('<sfile>')")).parent
    pack_dir = str(this_dir.parent.parent.parent)
    if pack_dir not in sys.path:
       sys.path.append(pack_dir)


def VPE_run_this_as_py():
    """Run a Python shadow of the current Vim script.

    For example, if invoked from .vim/syntax/mysyntax.vim then
    .vim/syntax/mysyntax.py is imported its 'run()' function invoked.
    """
    # Use imports within function to minimise global namespace polution.
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
