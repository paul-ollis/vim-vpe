python3 << trim EOF

    import os
    import platform
    import sys
    from pathlib import Path

    def _update_sys_path():
        # If we seem to have a virtual environment in the Vim config tree then
        # isert it at the start of sys.path.
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

    import vpe
    vpe.post_init()
EOF

Vpe install
exit!
