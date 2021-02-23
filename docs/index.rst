Introduction
============

::

                _    ______  ______
               | |  / / __ \/ ____/
               | | / / /_/ / __/
               | |/ / ____/ /___     The Vim Python Extensions
               |___/_/   /_____/

VPE adds to Vim's built-in support for Python scripting with the following
aims.

- Ability to write more Pythonic code.

- Provide a toolkit of additional classes and functions to support complex
  plug-ins.

- Be extremely compatible with existing Vim Python scripts.


.. toctree::
    :maxdepth: 1

    plugins
    api/api.vpe


Requirements
------------

VPE requires a minimum of Vim 8.0.0700 and Python 3.6.


Installation
------------

The VPE directory tree is structured as a package with a single plugin.
Assuming your Vim files are in the "~/.vim" directory, add a "pack"
sub-directory and install VPE into the "~/.vim/pack" directory. One way to do
this is by simply cloning the VPE repository.
::

    $ cd ~/.vim/pack
    $ git clone https://github.com/paul-ollis/vim-vpe.git

or just unzip vim-vpe.zip.
::

    $ cd ~/.vim/pack
    $ unzip vim-vpe.zip

The package includes a "vim-vpe/start/vpe/plugin/vpe.vim" startup script that
updates the Python path so that the *vpe* package can be imported.


Quick start
-----------

The quickest way to start using VPE is to import the :attr:`vim` object:

.. code:: python

    from vpe import vim

The :attr:`vim` object is an instance of the `vpe.Vim` class and is intended to
be a drop in replacement for Vim's standard :vim:`python-vim` module, but with
a number of enhancements.

- Most of Vim's functions appear as members, for example:

  .. code:: python

      vim.cursor(4, 10)            # Position cursor at row 4, column 10.
      m = vim.execute('messages')  # Get all the recent Vim messagse.

- The attributes buffers, current, options, tabpages, vars, vvars and windows
  provide enhanced access to the corresponding Vim objects. For example
  vim.current.buffer provides a `Buffer` instance in place of Vim's standard
  :vim:`python-buffer`.

- The Vim registers are available using the `registers<Vim.registers>`
  attribute.

- When errors occur a `VimError` is raised, which provides a better breakdown
  of the error. This is a subclass of vim.error (:vim:`python-error`) so
  existing code that catches vim.error still works.


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
  <https://vimhelp.org/popup.txt.html#popup-window>`_. (Requires Vim 8.2.)

- Pythonic support for using
  `timers <https://vimhelp.org/eval.txt.html#timers>`_.

- Pythonic support for `autocommands
  <https://vimhelp.org/autocmd.txt.html#autocommands>`_ that invoke Python
  functions.

- Python support for `channels <https://vimhelp.org/channel.txt.html>`_.

- Logging to a buffer. Useful when developing and debugging plug-ins.
