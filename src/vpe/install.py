"""Script to 'install' VPE.

This installs $HOME/.vim/plugin/000-vpe.vim, which performs the Vim plugin
actions required by the Vim Python Extensions. It also installs the VPE help
file and generates its tags.
"""

import os
import platform

from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

from vpe import call_soon, common, echo_msg, vim


def report(*args) -> None:
    """Write to the Vim terminal."""
    call_soon(echo_msg, *args)


def locate_vim_dir() -> tuple[str, bool]:
    """Locate the directory that should contain Vim config files.

    This is a bit tricky because Vim tries to be flexible and different
    platforms have different rules.

    :return:
        A tuple of a ``Path`` of the Vim config directory and a bool flag that
        is ``True`` if the path was determined with high confidence.
    """
    # Vim should have set $MYVIMDIR, unless no directory is present.
    vimdir_pathname = os.environ.get('MYVIMDIR', '')
    ok = True
    if not vimdir_pathname:
        # Looks like we will be creating a Vim configuration directory tree,
        # which is platform dependent.
        if platform.system() == 'Windows':
            vimdir = Path('~/vimfiles').expanduser()
        elif platform.system() == 'Linux':
            vimdir = Path('~/.vim').expanduser()
        else:
            # We really should try harder, but ~/.vim is a tolerable fallback
            # and at least the user will have some installed files: they may
            # just have to move them.
            vimdir = Path('~/.vim').expanduser()
            ok = False
    else:
        vimdir = Path(vimdir_pathname)

    return vimdir, ok


def install_000():
    """Install the 000-vpe.vim plugin file."""
    vim_init_dir, _ = locate_vim_dir()
    vim_plugin_dir = vim_init_dir / 'plugin'
    vim_plugin_dir.mkdir(parents=True, exist_ok=True)
    vimfile = '000-vpe.vim'
    vpe_zero_src_trav: Traversable = files(
        'vpe.resources').joinpath(vimfile)
    vpe_zero_dst_path = vim_plugin_dir / vimfile

    vpe_zero_dst_path.write_text(
        vpe_zero_src_trav.read_text(encoding='utf-8'),
        encoding='utf-8')
    report(f'Installed {vpe_zero_dst_path}')


def install_help():
    """Install the VPE help file."""
    vim_init_dir, _ = locate_vim_dir()
    vim_doc_dir = vim_init_dir / 'doc'
    vim_doc_dir.mkdir(parents=True, exist_ok=True)

    docfile = 'vpe-help.txt'
    doc_src_trav: Traversable = files(
        'vpe.resources').joinpath(docfile)
    doc_dst_path = vim_doc_dir / docfile

    doc_dst_path.write_text(
        doc_src_trav.read_text(encoding='utf-8'),
        encoding='utf-8')
    doc_dir = vim_init_dir / 'doc'
    try:
        vim.command(f'helptags {doc_dir}')
    except common.VimError as e:
        report(f'Helptags: {e}')
    report(f'Installed {doc_dst_path}')


def run():
    """Perform the installation of Vim init code and help."""
    vim_init_dir, ok = locate_vim_dir()
    if not ok:
        report(f'Platform {platform.system()!r} detected.')
        report('The chosen instation directory may be incorrect. Please')
        report('move the file if necessary and report this on')
        report('https://github.com/paul-ollis/vim-vpe/issues')
    report(f'Using configuration directory: {vim_init_dir}')

    install_000()
    install_help()


if __name__ == '__main__':
    run()
