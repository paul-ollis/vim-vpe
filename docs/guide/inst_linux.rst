Installation on Linux
---------------------

It is recommended that you use a Python virtual environment for VPE. The
following instructions assume this approach. The virtual environment should be
placed within your Vim configuration directory tree, specifically one of:

1. $HOME/.vim/lib/python

2. $HOME/.config/vim/lib/python

Option 1 is currently the more common. Option 2 is only available on platforms
that support XDG and is only supported by fairly recent versions of Vim. So use
option 1 unless you know better. Option 1 is assumed here.

The following instructions use Python's built-in ``venv`` module. If you prefer
another tool, such as ``uv`` then you should be able to adapt the procedure.


For the first ever installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If this is your first VPE installation then you need to:

1.  Create the virtual environment.

    .. code-block:: bash

        # Make sure you are in your $HOME directory
        python -m venv .vim/lib/python

        # Activate the virtual environment.
        source .vim/lib/python/bin/activate

        # Install VPE.
        python -m pip install vim-vpe

2.  Without leaving the virtual environment you activated above, start Vim.

3.  Within your Vim session enter the commands.

    .. code-block:: vim

        py3 import vpe
        py3 vpe.post_init()
        Vpe install

        " To see what was done
        messages

    This installs a file called 000-vpe.vim in you Vim plugin directory and also
    a help file.

4.  Exit the virtual environment.

    .. code-block:: bash

        deactivate

.. sidebar:: 000-vpe.vim

    The reason for using the name 000-vpe.vim is to make sure that VPE is
    fully initialised *very* early on. This means that other Vim plugins can
    make use of VPE if desired.

You will only need to activate in the future to upgrade VPE.


For upgrades
~~~~~~~~~~~~

1.  Activate the virtual environment, upgrade VPE then exit the environment.

    .. code-block:: bash

        # Make sure you are in your $HOME directory
        source .vim/lib/python/bin/activate
        python -m pip install --upgrade vim-vpe
        deactivate

2.  Within a new Vim session enter the commands.

    .. code-block:: vim

        Vpe install

    This updates the 000-vpe.vim file and help file.
