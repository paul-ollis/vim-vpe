Installation on Windows
-----------------------

For the first ever installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A user install is recommended as used in the following instructions.

If this is your first VPE installation then you need to:

1.  Install the VPE package.

    .. code-block:: bash

        python -m pip install --user vim-vpe

2.  Start a new Vim session and run the following commands.

    .. code-block:: vim

        py3 import vpe
        py3 vpe.post_init()
        Vpe install

    This installs a file called 000-vpe.vim in you Vim plugin directory and also
    a help file.

.. sidebar:: 000-vpe.vim

    The reason for using the name 000-vpe.vim is to make sure that VPE is
    fully initialised *very* early on. This means that other Vim plugins can
    make use of VPE if desired.


For upgrades
~~~~~~~~~~~~

1.  Perform an upgrade install of VPE.

    .. code-block:: bash

        python -m pip install ---user --upgrade vim-vpe
        deactivate

2.  Within a new Vim session enter the commands.

    .. code-block:: vim

        Vpe install

    This updates the 000-vpe.vim file and help file.
