::

                 _    ______  ______
                | |  / / __ \/ ____/
                | | / / /_/ / __/     The Vim Python Extensions
                | |/ / ____/ /___
                |___/_/   /_____/


:status:
    It must considered alpha, but I am personally using VPE to configure nearly
    all of my Vim environment and for some quite complex plug-ins.


Introduction
============

The Vim Python Extensions plugin adds a layer on top of Vim's built-in Python
support.


Quick start
-----------

The quickest way to start using VPE is to import the `vim` object:

.. code:: python

    from vpe import vim

The `vim` object is an instance of the `Vim` class and is intended to be a drop
in replacement for Vim's standard `python-vim
<https://vimhelp.org/if_pyth.txt.html#python-vim>`_ module, but with a number
of enhancements.

- Most of Vim's functions appear as members, for example:

  .. code:: python

      vim.cursor(4, 10)            # Position cursor are row 4, column 10.
      m = vim.execute('messages')  # Get all the recent Vim messagse.

- The attributes buffers, current, options, tabpages, vars, vvars and windows
  provide enhanced access to the corresponding Vim objects. For example
  vim.current.buffer provides a `Buffer` instance in place of Vim's standard
  `python-buffer <https://vimhelp.org/if_pyth.txt.html#python-buffer>`_. This
  supports things like easier access to buffer variables, more efficient buffer
  modification and per-buffer metadata storage.

- The Vim registers are available using the `registers` attribute.

- When errors occur a `VimError` is raised, which provides a better breakdown
  of the error (code and command are available as attributes). This is a
  subclass of `vim.error <https://vimhelp.org/if_pyth.txt.html#python-error>`_
  so existing code that catches vim.error still works.
  

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

- Pythonic support for using `timers <https://vimhelp.org/eval.txt.html#timers>`_.

- Pythonic support for `autocommands
  <https://vimhelp.org/autocmd.txt.html#autocommands>`_ that invoke Python
  functions.

- Python support for `channels <https://vimhelp.org/channel.txt.html>`_.

- Logging to a buffer. Useful when developing and debugging plug-ins.
