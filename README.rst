::

                 _    ______  ______
                | |  / / __ \/ ____/
                | | / / /_/ / __/     The Vim Python Extensions
                | |/ / ____/ /___
                |___/_/   /_____/


:status:
    This is version 0.7.0-a.

    The Version 0.7 line is intended to be the stepping stone for version 1.0.

    Although it has not yet reached a version 1.0 release, I make heavy, daily
    use of VPE within my Vim environment without problems.

    While the API should be considered unstable, it has actually proven fairly
    stable, with only a few, minor incompatible changes since version 0.1.


Introduction
============

VPE provides a toolkit of modules and classes aimed at making it easier to
extend ``Vim`` using modern Pythonic code. Its key features are:

- A ``Vim`` class and corresponding ``vim`` singleton which provides an API
  that is is extremely compatible with Vim's built-in ``vim`` module, but
  includes extended capabilities.

- The ``vpe`` package, containing additional modules and classes which provide:

  - More pythonic APIs for some Vim features.
  - Extension modules and classes to help in writing plugins in Python.

- You can extend Vim using much more Pythonic code than is possible using only
  Vim's built-in ``vim`` module.

- Support for plugins, using Python's standard library entry-point mechanism.

- Buffer based logging support with optional stdout/stderr redirection, which
  can be invaluable for debugging your code.


Quick start
-----------

This is just a brief introduction. For more complete documentation see the
`online documentation`_.


Installation
~~~~~~~~~~~~

If you have a pre 0.7 VPE installation then head on over to

    https://vim-vpe.readthedocs.io/en/latest/#installation

for details on removing that version.

.. code-block:: bash

    python -m pip install --user git+https://github.com/paul-ollis/vim-vpe.git

On some systems you may have to add the ``--break-system-packages`` option.
(VPE does not pull in other Python packages, so your system is safe.)

At this point you should be able to run Vim and enter the command ``Vpe
version`` to verify the basic installation has worked.

Then install Vim initialisation support code and the Vim help file. From within
Vim run the commands:

.. code-block:: vim

    py3 import vpe.install
    py3 vpe.install.run()


Using VPE
~~~~~~~~~

The quickest way to start using VPE is to import the `vim` object:

.. code:: python

    from vpe import vim

The `vim``` object is an instance of the `Vim` designed as a drop in
replacement for Vim's standard `python-vim`_ module, but with a number of
enhancements.

- Most of Vim's functions appear as members, for example:

  .. code:: python

      vim.cursor(4, 10)            # Position cursor at row 4, column 10.
      m = vim.execute('messages')  # Get all the recent Vim messages.

- The attributes buffers, current, options, tabpages, vars, vvars and windows
  provide enhanced access to the corresponding Vim objects. For example
  vim.current.buffer provides a `Buffer` instance in place of Vim's standard
  `python-buffer`_. This supports things like easier access to buffer
  variables, more efficient buffer modification and per-buffer metadata
  storage.

- The Vim registers are available using the `registers` attribute.

- When errors occur a `VimError` is raised, which provides a better breakdown
  of the error (code and command are available as attributes). This is a
  subclass of `vim.error <https://vimhelp.org/if_pyth.txt.html#python-error>`_
  so existing code that catches vim.error still works.

.. _python-vim: https://vimhelp.org/if_pyth.txt.html#python-vim
.. _python-buffer: https://vimhelp.org/if_pyth.txt.html#python-buffer
.. _online documentation: https://vim-vpe.readthedocs.io


Features
--------

This is a brief list of VPE's features.

- A `Vim` class that provides an enhanced, drop-in replacement for the standard
  `python-vim <https://vimhelp.org/if_pyth.txt.html#python-vim>`_ module.

- Classes `Window`, `Buffer`, `TabPage` are enhanced wrappers around the
  standard `vim <https://vimhelp.org/if_pyth.txt.html#python-vim>`_ versions.

- Support for cleanly invoking Python functions for keyboard `mappings
  <https://vimhelp.org/map.txt.html#:nmap>`_.

- Pythonic support for using `popup-windows
  <https://vimhelp.org/popup.txt.html#popup-window>`_.

- Pythonic support for using
  `timers <https://vimhelp.org/eval.txt.html#timers>`_.

- Pythonic support for `autocommands
  <https://vimhelp.org/autocmd.txt.html#autocommands>`_ that invoke Python
  functions.

- Pythonic support for `channels <https://vimhelp.org/channel.txt.html>`_.

- Logging to a buffer. Useful when developing and debugging plug-ins.
