Installation
============

The Vim Python Extensions (VPE) are, of course, written in Python and for
version 0.7 and newer installation VPE is installed as a standard Python
package. The details of how to do this depend a bit on your operating system
and this guide provides separate OS specific chapters.

If you have a pre 0.7 VPE installation then head on over to

    https://vim-vpe.readthedocs.io/en/latest/#installation

for details on removing that version.


.. toctree::
    :maxdepth: 2

    inst_linux.rst
    inst_windows.rst


Installation problems
~~~~~~~~~~~~~~~~~~~~~

If your Vim uses a different Python version
...........................................

It may be that your Vim installation uses a different version of Python to the
default for your operating system, in which case the basic installation may
appear to work, but the `vpe` module will not be importable within Vim.

To fix this run the following within Vim to find the correct Python executable
and version for your Vim installation.

.. code-block:: vim

    py3 import sys
    py3 print(sys.executable)
    py3 print(sys.version)

Then use the correct Python executable in the above installation instructions.
For example, if the above commands printed something like::

    /usr/local/bin/python3
    3.11.3 (tags/v3.11.3:f3909b8bc8, Apr 20 2023, 18:55:17) [GCC 11.3.0]

Then you would create the vitual environment as:

.. code-block:: bash

    /usr/local/bin/python3.11 -m venv .vim/lib/python


.. _remove_pre_07:

A pre 0.7 version of VPE in installed
.....................................

Your pre 0.7 VPE is probably installed in::

    $ $HOME/.vim/pack/vim-vpe

But you may have chosen to a slightly different location.

Remove the ``vim-vpe`` directory to uninstall.

You may also want to review your $HOME/.vim/vimrc and similar files in case you
have initialisation that makes assumptions about your VPE installation.


Tweaking the behaviour of 000-vpe.vim
.....................................

The 000-vpe.vim script runs some code that injects the `vpe` and `vim<vpe.vim>`
objects into Vim's Python namespace and the Python interpreter's builtin
namespace. This matches how VPE worked before version 0.7. However this
is rather invasive and quite possibly not what you really want.

This behaviour can be controlled using configuration values stored in a global
``vpe_config`` dictionary. To do this you should create the configuration in
your $HOME/.vimrc or $HOME/.vim/vimrc file. Edit your vimrc file, place the
cursor at a suitable location and run the command:

.. code-block:: vim

    :Vpe insert_config

The comments inserted with the code should provide all necessary explanation.
