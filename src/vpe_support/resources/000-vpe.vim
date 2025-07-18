" Initialisation for VPE - Vim Python Extensions.
"
" Warning:
"     This file is created by the vpe-install script. You should not need to
"     edit this file and, if you do, re-running vpe-install will lose your
"     changes.

" Only run once.
if exists('g:loaded_vpe')
  finish
endif
let g:loaded_vpe = 1

" Run a Python script that shadows the current Vim script.
"
" For example, if invoked from .vim/syntax/mysyntax.vim then
" .vim/syntax/mysyntax.py is imported and its 'run()' function invoked.
"
" This provides a way to hook Python code into Vim's various hook script
" mechanisms.
command! VPERunThisAsPy call py3eval('VPE_run_this_as_py()')


" ----------------------------------------------------------------------------
" The rest of this run's as Python code.
" ----------------------------------------------------------------------------

python3 << trim EOF

    # Import the vpe package. This preforms most of the initialisation...
    import vpe

    # ...and vpe.post_init() finishes off, including loading plugins. Enable
    # log redirection for 'post_init()'. This prevents printing in plugin
    # initialisation from polluting the terminal.
    vpe.log.redirect()
    try:
        vpe.post_init()
    finally:
        vpe.log.unredirect()

    # Mapping to capture python files that have already impported by
    # `VPE_run_this_as_py`.
    VPE_run_as_imports = {}

    # TODO:
    #     This is fragile. I would like a stop using it.
    #     Is this offically supposed to be part of VPE?
    def VPE_run_this_as_py():
        """Run a Python shadow of the current Vim script.

        For example, if invoked from .vim/syntax/mysyntax.vim then
        .vim/syntax/mysyntax.py is imported and its 'run()' function invoked.

        This mechanism may become unnecessary with VPE 0.7 and beyond. But it will
        continue to be provided for backward compatibility.
        """

        # Use imports within function to minimise global namespace polution.
        from importlib.machinery import SourceFileLoader
        from importlib.util import spec_from_loader, module_from_spec
        from pathlib import Path

        import vim as _vim

        try:
            this_script = Path(_vim.eval("expand('<sfile>')"))
            py_path = this_script.with_suffix('.py')
            if py_path in VPE_run_as_imports:
                module = VPE_run_as_imports[py_path]
            else:
                mod_name = py_path.stem
                loader = SourceFileLoader(mod_name, str(py_path))
                spec = spec_from_loader(loader.name, loader)
                module = module_from_spec(spec)
                spec.loader.exec_module(module)
                VPE_run_as_imports[py_path] = module
            module.run()

        except Exception as e:
            import traceback
            import io
            import vpe
            f = io.StringIO()
            traceback.print_exc(file=f)
            s = ['VPE_run_this_as_py Failure:']
            s.append(f'    {this_script=}')
            s.append(f'    {py_path=}')
            s.append(f'    mod_name={loader.name}')
            s.append(f.getvalue())
            vpe.log('\n'.join(s))

        return ''


    def provide_backward_compatibilty():
        """Make sure that old behaviour continues, unless disabled.

        Before version 0.7, the `vpe` module and `Vim` singleton (`vim`) were
        inserted unconditionally into Vim's Python namespace and into the Python
        interpreter's builtins namspace.

        Since 0.7, a set of global variable can be used to selectively prevent
        aspects of this behaviour.

        ``g:vpe_do_not_auto_import``
            Prevents any of the imports/namespace insertions. This is equivalent
            to setting all the below variable to a true value.

        ``g:vpe_do_not_auto_import_vpe``
            Prevents `vpe` being imported into Vim's python namespace.

        ``g:vpe_do_not_auto_import_vim``
            Prevents `vim` (the `Vim` singleton) being imported into Vim's python
            namespace.

        ``g:vpe_do_not_auto_import_vpe_into_builtins``
            Prevents `vpe` being imported into Pythons's builtins namespace.

        ``g:vpe_do_not_auto_import_vim_into_builtins``
            Prevents `vim` (the `Vim` singleton) being imported into Python's
            builtins namespace.

        A variable must be set to a 'truthy' value to block the import/insertion.
        """
        import builtins
        import vim as _vim

        if _vim.vars.get('vpe_do_not_auto_import', False):
            return

        import vpe
        from vpe import vim

        # Import `vpe` into Vim's Python namespace.
        if not _vim.vars.get('vpe_do_not_auto_import_vpe', False):
            _vim.command('python3 import vpe')

        # Import `vim` singleton into Vim's Python namespace. Make the built-in
        # ``vim`` module available as ``_vim``.
        if not _vim.vars.get('vpe_do_not_auto_import_vim', False):
            _vim.command('python3 import vim as _vim')
            _vim.command('python3 from vpe import vim')

        if not _vim.vars.get('vpe_do_not_auto_import_vpe_into_builtins', False):
            builtins.vpe = vpe

        if not _vim.vars.get('vpe_do_not_auto_import_vim_into_builtins', False):
            builtins.vim = vim


    # Invoke initialisation functions.
    provide_backward_compatibilty()

    # Clean up the Vim Python namespace.
    del provide_backward_compatibilty

EOF
