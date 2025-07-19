"""Script to 'install' VPE.

This simply installs $HOME/.vim/plugin/000-vpe.vim, which performs the Vim
plugin aspects required by the Vim Python Extensions.
"""

from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

from vpe import common, vim


def run():
    """Perform the installation of Vim init code and help."""
    vim_init_dir = Path.home() / '.vim'
    vim_plugin_dir = vim_init_dir / 'plugin'
    vim_doc_dir = vim_init_dir / 'doc'
    vim_plugin_dir.mkdir(parents=True, exist_ok=True)
    vim_doc_dir.mkdir(parents=True, exist_ok=True)

    # Install the initialisation plugin.
    vimfile = '000-vpe.vim'
    vpe_zero_src_trav: Traversable = files(
        'vpe.resources').joinpath(vimfile)
    vpe_zero_dst_path = vim_plugin_dir / vimfile

    vpe_zero_dst_path.write_text(
        vpe_zero_src_trav.read_text(encoding='utf-8'),
        encoding='utf-8')
    print(f'Installed {vpe_zero_dst_path}')

    # Install the VPE help file.
    docfile = 'vpe-help.txt'
    doc_src_trav: Traversable = files(
        'vpe.resources').joinpath(docfile)
    doc_dst_path = vim_doc_dir / docfile

    doc_dst_path.write_text(
        doc_src_trav.read_text(encoding='utf-8'),
        encoding='utf-8')
    try:
        vim.command('helptags ~/.vim/doc')
    except common.VimError as e:
        print(f'Helptags: {e}')
    print(f'Installed {doc_dst_path}')


if __name__ == '__main__':
    run()
