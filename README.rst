::

                 _    ______  ______
                | |  / / __ \/ ____/
                | | / / /_/ / __/     The Vim Python Extensions
                | |/ / ____/ /___
                |___/_/   /_____/

Welcome to the Vim Python Extensions (VPE).

:status:
    This is version 0.7.0

    The Version 0.7 line is intended to be the stepping stone for version 1.0.

    Although it has not yet reached a version 1.0 release, I make heavy, daily
    use of VPE within my Vim environment without problems.

    While the API should be considered unstable, it has actually proven largely
    stable, with only a few, minor incompatible changes since version 0.1.


Introduction
============

VPE provides a toolkit of modules and classes aimed at making it easier to
extend ``Vim`` using modern Pythonic code. The headline features are:

- Instead of using the standard ``vim`` module you can use the ``vpe.vim``
  object, which provides a greatly extended superset of the ``vim`` module's
  features.

- Other extensions that, along with ``vpe.vim``, just make it easier to
  write Pythonic plugin code for Vim.


Installation
------------

Read the `installation instructions online`_.


Using VPE
---------

This is just a brief introduction. For more complete documentation see the
`online documentation`_.

The quickest way to start using VPE is to import the `vim` object:

.. code:: python

    from vpe import vim

The ``vim`` object is an instance of the ``Vim`` class, which is designed as a
drop in replacement for Vim's standard `python-vim`_ module, but with a number
of enhancements, including:

- Most of Vim's functions appear as members, for example:

  .. code:: python

      vim.cursor(4, 10)            # Position cursor at row 4, column 10.
      m = vim.execute('messages')  # Get all the recent Vim messages.

- The attributes buffers, current, options, tabpages, vars, vvars and windows
  provide enhanced access to the corresponding Vim objects. For example
  vim.current.buffer provides a `Buffer`_ instance in place of Vim's standard
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
.. _online documentation:
     https://vim-vpe.readthedocs.io/en/latest
.. _installation instructions online:
     https://vim-vpe.readthedocs.io/en/latest/installation.html


Features
--------

This is a brief list of VPE's features.

- The `vpe.vim`_ object - a much enhanced replacement for the standard ``vim``
  module (`python-vim <https://vimhelp.org/if_pyth.txt.html#python-vim>`_).
  This is an instance of the `Vim class`_.

- Classes `Window`_, `Buffer`_, `TabPage`_ are enhanced wrappers around the
  standard (`vim <https://vimhelp.org/if_pyth.txt.html#python-vim>`_) versions.

- `Key mappings`_ can cleanly be set up to invoke Python functions and methods.

- `User commands`_ can cleanly be set up to invoke Python functions and methods.
  VPE also provides support for subcommands and automatic command line tab-key
  completion.

- `Timers`_ can cleanly be set up to invoke Python functions and methods.

- Autocmd `Events`_ can cleanly be set up to invoke Python functions and methods.

- A `built in log`_, which is useful for debugging plugin code.

  - The log can be displayed in a dedicated Vim buffer.
  - Printing can be redirected to the log.
  - You can create your own plugin specific log(s).

- Pythonic support for using `popup windows`_.

- Pythonic support for `channels`_.

.. _Buffer: https://vim-vpe.readthedocs.io/en/latest/api/api.vpe.html#vpe.Buffer
.. _TabPage: https://vim-vpe.readthedocs.io/en/latest/api/api.vpe.html#vpe.TabPage
.. _Vim class: https://vim-vpe.readthedocs.io/en/latest/api/api.vpe.html#vpe.Vim
.. _vpe.vim: https://vim-vpe.readthedocs.io/en/latest/api/api.vpe.html#vpe.vim
.. _Window: https://vim-vpe.readthedocs.io/en/latest/api/api.vpe.html#vpe.Window
.. _Key mappings: https://vim-vpe.readthedocs.io/en/latest/mapping.html
.. _User commands: https://vim-vpe.readthedocs.io/en/latest/user-commands.html
.. _built in log: https://vim-vpe.readthedocs.io/en/latest/logging.html
.. _Timers: https://vim-vpe.readthedocs.io/en/latest/timers.html
.. _Events: https://vim-vpe.readthedocs.io/en/latest/auto-commands.html
.. _popup windows: https://vim-vpe.readthedocs.io/en/latest/api/api.vpe.html#vpe.Popup
.. _channels: https://vim-vpe.readthedocs.io/en/latest/api/api.vpe.channels.html
