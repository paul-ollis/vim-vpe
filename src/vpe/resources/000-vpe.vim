" Initialisation for VPE - Vim Python Extensions.
"
" Warning:
"     This file is created by the vpe-install script. Any edits to the file
"     will be over-written the next time you start a Vim session.

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

" Check for and enable code in vritual environment installation in
" $HOME/.vim/lib/python or its equivalent.
"
" This provides support for the recommended way of installing VPE; i.e. within
" a virtual environment within Vim's configuration directory tree.
python3 << trim EOF

    def _update_sys_path():
        # Do imports inside the function to minimise namespace pollution.
        import os
        import platform
        import sys
        from pathlib import Path

        vimdir_pathname = os.environ.get('MYVIMDIR', '')
        if not vimdir_pathname:
            # This should mean that there is no Vim configuration directory
            # tree, according to the documents. However, I have seen this
            # unset when a ~/.vim tree exists. So, the strategy here is to
            # check for actual existence of candidate Vim configuration
            # directories.
            if platform.system() == 'Windows':
                vimdir = Path('~/vimfiles').expanduser()
            elif platform.system() == 'Linux':
                vimdir = Path('~/.vim').expanduser()
                if not vimdir.is_dir():
                    vimdir = Path('~/.config/vim').expanduser()
            else:
                # Assume a Linux style environment.
                vimdir = Path('~/.vim').expanduser()
                if not vimdir.is_dir():
                    vimdir = Path('~/.config/vim').expanduser()
        else:
            vimdir = Path(vimdir_pathname)
        if not vimdir.is_dir():
            # Now this is uber-unlikely, but were it ever to occur then
            # we should just give up.
            return

        vim_pylib_path = vimdir / 'lib' / 'python'
        if not vim_pylib_path.is_dir():
            return
        config_path = vim_pylib_path / 'pyvenv.cfg'
        if not config_path.is_file():
            return

        x, y = sys.version_info[:2]
        site_path = vim_pylib_path / 'lib' / f'python{x}.{y}' / 'site-packages'
        if not site_path.is_dir():
            return

        site_pathname = str(site_path)
        if site_pathname not in sys.path:
            sys.path[0:0] = [site_pathname]

    _update_sys_path()
    del _update_sys_path

EOF

" Now import and initialise VPE.
python3 << trim EOF

    # Import the vpe package. This performs most of the initialisation...
    import vpe

    # ...and vpe.post_init() finishes off, including loading plugins. Enable
    # log redirection for 'post_init()'. This prevents printing in plugin
    # initialisation from polluting the terminal.
    vpe.log.redirect()
    try:
        vpe.post_init()
    finally:
        vpe.log.unredirect()

    # Mapping to capture python files that have already imported by
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

        from vpe import vim

        def init_config_var(name: str, default_value: int) -> None:
            section = vim.vars.vpe_config
            parts = name.split('.')
            for part in parts[:-1]:
                if part not in section:
                    section[part] = {}
                section = section[part]
            leaf = parts[-1]
            if leaf not in section:
                section[leaf] = default_value

        if 'vpe_config' not in vim.vars:
            vim.vars.vpe_config = {}
        init_config_var('import.vpe', 1)
        init_config_var('import.vim', 1)
        init_config_var('import.vpe_into_builtins', 1)
        init_config_var('import.vim_into_builtins', 1)

        # Import `vpe` into Vim's Python namespace.
        imp = vim.vars.vpe_config['import']
        if imp['vpe']:
            vim.command('python3 import vpe')

        # Import `vim` singleton into Vim's Python namespace. Make the
        # built-in ``vim`` module available as ``_vim``.
        if imp['vim']:
            vim.command('python3 import vim as _vim')
            vim.command('python3 from vpe import vim')

        # Optionally make ``vpe`` available in the Python builtin namespace.
        if imp['vpe_into_builtins']:
            builtins.vpe = vpe

        # Optionally make ``vim`` available in the Python builtin namespace.
        if imp['vim_into_builtins']:
            builtins.vim = vim


    # Invoke initialisation functions.
    vpe.log.redirect()
    try:
        provide_backward_compatibilty()
    finally:
        vpe.log.unredirect()

    # Clean up the Vim Python namespace.
    del provide_backward_compatibilty

EOF
