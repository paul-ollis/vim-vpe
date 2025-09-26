"""VPE installation script for Linux and Windows"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path


def run_command(args: list[str]) -> bool:
    """Run a command and check success.

    Print any error output and return False if the command fails.
    """
    err = None
    try:
        ret = subprocess.run(
            args, capture_output=True, encoding='utf-8', check=False)
    except Exception as e:
        err = e
        ret = None

    if ret is None or ret.returncode != 0:
        print('Command execution failed')
        if err is not None:
            print(f'   {err}')
        print(f'   Name: {args[0]}')
        for i, arg in enumerate(args[1:]):
            print(f'   Arg[{i + 1}]: {arg!r}')
        if ret and ret.stdout.strip():
            print('   Command output:')
            for line in ret.stdout.splitlines():
                print(f'     {line.rstrip()}')
        if ret and ret.stdout.strip():
            print('   Command errors:')
            for line in ret.stderr.splitlines():
                print(f'     {line.rstrip()}')
        return False

    else:
        return True


def find_vimdir() -> tuple[Path, bool]:
    """Try to work out the correct Vim directory tree.

    This only returns if a directory name can be determined.
    """
    ok = True

    if platform.system() == 'Windows':
        vimdir = Path('~/vimfiles').expanduser()
        ok = vimdir.is_dir()

    elif platform.system() == 'Linux':
        vimdir = Path('~/.config/vim').expanduser()
        if not vimdir.is_dir():
            vimdir = Path('~/.vim').expanduser()
        ok = vimdir.is_dir()

    else:
        print(f'Unsupported system: {platform.system()}')
        sys.exit(1)

    if not ok and vimdir.exists():
        print(f'The file {vimdir} exists, but')
        print('it does not appear to be a directory. Please fix and try again')
        sys.exit(1)

    return vimdir, ok


def get_pip_command_base(vimdir) -> list[str]:
    """Work out the base command for Pip install operations.

    On Linux this creates a virtual envronment if it does not already exist.

    :return:
        The Python command arguments that should be used for installation. On
        Linux this will use the Python executable in the virtual environment.
    """
    if platform.system() == 'Windows':
        return [sys.executable, '-m', 'pip', 'install', '--user']

    # Trying to create an existing virtual enironment is OK.
    venvdir = vimdir / 'lib' / 'python'
    if not run_command(['python', '-m', 'venv', str(venvdir)]):
        return []

    py_prog = venvdir / 'bin' / 'python'
    return [str(py_prog), '-m', 'pip', 'install']


def test_vim_prog(vim_prog) -> None:
    """Check that Vim can be run."""
    if not run_command([vim_prog, '--version']):
        print(f'Cannot run {vim_prog}.')
        sys.exit(1)


def find_vim_prog() -> str:
    """Try find the Vim program."""
    if platform.system() == 'Linux':
        # There is a good chance that Vim is in the user's $PATH.
        if run_command(['vim', '--version']):
            return 'vim'
    else:
        for ver in ['vim90', 'vim91']:
            exe = Path(rf'C:\Program Files\Vim\{ver}\vim.exe')
            if exe.exists():
                return str(exe)

    print('Could not work out where your Vim program lives.')
    print('Use the --vim-path option to specify.')
    sys.exit(1)


def install_vpe_plugin(vim_prog: str) -> None:
    """Try to install the VPE plugin."""
    vim_script = Path('inst-vpe.vim')    # pylint: disable=redefined-outer-name

    if not run_command([vim_prog, '-c', f'source {vim_script}']):
        print('The VPE library may not be properly set up. See')
        print(
            '  https://vim-vpe.readthedocs.io/en/latest/installation.html')
        print('for instructions on how to install VPE')
        sys.exit(1)


def main(args: argparse.Namespace) -> None:
    """Perform the installation if possible."""
    if not args.vim_path:
        print('Trying to find the Vim program...')
        vim_prog = find_vim_prog()
    else:
        vim_prog = args.vim_path
        test_vim_prog(vim_prog)

    print("Working out what Vim's configuration directory is...")
    vimdir, ok = find_vimdir()
    if not ok:
        # We have a directory name, but it does not exist. Only create if the
        # user says so.
        if not args.make_vim_dir:
            print(f'The file {vimdir} does not exist.')
            print('Re-run with "--make-vim-dir" to force its creation.')
            sys.exit(1)
        try:
            vimdir.mkdir(parents=True)
        except OSError as e:
            print(f'Could not create directory {vimdir}')
            print(e)
            sys.exit(1)

    # Work out the correct way to install packages.
    print('Working out how to install Python packages and libraries...')
    pip_base = get_pip_command_base(vimdir)
    if not pip_base:
        sys.exit(1)

    # Install VPE.
    print('Installing VPE...')
    if not run_command(pip_base + ['--upgrade', 'vpe']):
        sys.exit(1)

    # Make sure that the VPE plugin is correctly installed.
    print("Ensuring VPE's plugin code is installed...")
    install_vpe_plugin(vim_prog)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Install VPE and its Vim plugin component.')
    parser.add_argument(
        '--make-vim-dir', action='store_true',
        help='Create Vim config directory if required.')
    parser.add_argument(
        '--vim-path',
        help="Specify the Vim program's path.")

    parsed_args = parser.parse_args()

    vim_script = Path('inst-vpe.vim')
    if not vim_script.exists():
        print(f'Script {vim_script} not found')
        print('You must run this within the directory containing README.txt')
        sys.exit(1)

    main(parsed_args)
