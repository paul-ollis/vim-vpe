===============================
The Vim Python Extensions (VPE)
===============================

.. toctree::
    :maxdepth: 2

    api/vpe
    api/vpe.commands


Introduction
============

VPE adds to Vim's built-in support for Python scripting with the following
aims.

- Ability to write more Pythonic code.

- Provide a toolkit of additional classes and functions to support complex
  plug-ins.

- Be extremely compatible with existing Vim Python scripts.


Requirements
------------

VPE requires Vim 8.1 and Python 3.8. It has only be run on Linux.

It is intended that VPE will become compatible with Vim 8.0 and Python 3.6.
Testing on Windows is planned.


Installation
------------

TODO.


Quick start
-----------

The quickest way to start using VPE is to import the :attr:`vim` object:

.. code:: python

    from vpe import vim

The :attr:`vim` object is an instance of the `Vim` class and is intended to be a drop
in replacement for Vim's standard :vim:`python-vim` module, but with a number
of enhancements.

- Most of Vim's functions appear as members, for example:

  .. code:: python

      vim.cursor(4, 10)            # Position cursor are row 4, column 10.
      m = vim.execute('messages')  # Get all the recent Vim messagse.

- The attributes buffers, current, options, tabpages, vars, vvars and windows
  provide enhanced access to the corresponding Vim objects. For example
  vim.current.buffer provides a `Buffer` instance in place of Vim's standard
  :vim:`python-buffer`.

- The Vim registers are available using the `registers` attribute.

- When errors occur a `VimError` is raised, which provides a better breakdown
  of the error. This is a subclass of vim.error (:vim:`python-error`) so
  existing code that catches vim.error still works.
  

Features
--------

This is a brief list of VPE's features.

- A `Vim` class that provides an enhanced, drop-in replacement for the standard
  :vim:`python-vim` module.

- Classes `Window`, `Buffer`, `TabPage` are enhanced wrappers around the
  standard :vim:`if_pyth` versions.

- Support for cleanly invoking Python functions for keyboard mappings
  (:vim:`:nmap`), using a :vim:`popup-window`, :vim:`timers` 
  and :vim:`autocommands`.
