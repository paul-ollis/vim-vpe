            Welcome to the Vim Python Extensions (VPE) for Vim

This is a minimal download that provides a Python script to install VPE.
I cannot guarantee that the script will work reliably, especially on
Windows. So you may need to fallback to a manual installation. However, I would
be pleased to receive problem reports at:

    https://github.com/paul-ollis/vim-vpe/issues

so that I can fix any issues.

The install script is "install.py". The "inst-vpe.vim" script is used by
"install.py".

NOTE: You must be in the same directory as this README to run the script.

The install script has help.

    usage: Install VPE and its Vim plugin component. [-h] [--make-vim-dir]
                                                     [--vim-path VIM_PATH]

    options:
      -h, --help           show this help message and exit
      --make-vim-dir       Create Vim config directory if required.
      --vim-path VIM_PATH  Specify the Vim program's path.

The script may encounter fixable issues, such as not being able to find and run
your installed Vim program. It will try to provide a useful error message and
suggest which option might fix the problem.
