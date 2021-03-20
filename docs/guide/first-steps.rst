First steps
===========

Switching from the ``vim`` module
---------------------------------

If, as is quite likely, you have previously used Python for Vim scripting you
will be familiar with import the ``vim`` module.

.. code-block:: python

    import vim

The ``vim`` module provides many features supporting interaction with the
executing Vim program. Detail help is available - ``:help if_pyth.txt`` and
https://vimhelp.org/if_pyth.txt.html. The rest of this guide assumes that you
are reasonably familiar with this module.

In order to step up to using VPE, the starting point is to import ``vim`` from
`vpe`.

.. code-block:: python

    from vpe import vim

.. sidebar:: Use of vpe.vim in examples.

    The style ``from vpe import vim`` is recommended. However, the following
    examples use ``vpe.vim`` in order to distinguish from the ``vim`` module.

Then use this `vpe.vim` object instead of the ``vim`` module. The ``vim`` object
provided by `vpe` is an instance of the `Vim` class, which is designed to
provide almost exactly the same basic behaviour as the built-in ``vim`` module.
Of course, it is more than a simple replacement and the next sections cover
some of the important enhancements.


Vim Options
-----------

As well as accessing options using dictionary-like syntax, you can also access
options as attributes of ``vim.options``.

.. code-block:: python

    import vpe

    if vpe.vim.options['autoread']:  # Like vim.vim().options['autoread']
        ...

    if vpe.vim.options.autoread:     # Only works with vpe.vim.
        ...

The attribute access provides a more Pythonic approach and provides some
advantages.


String conversion
~~~~~~~~~~~~~~~~~

VPE automatically converts Unicode option values to strings, which greatly
simplifies a lot of code.

.. code-block:: python

    import vim
    import vpe

    vim.options['keywordprg']             # b'man -s'

    vpe.vim.options['keywordprg']         # 'man -s'
    vpe.vim.options.keywordprg            # 'man -s'

Note that one example where the `Vim` class chooses to behave slightly differently
to the ``vim`` module. Conversion from Unicode to strings is a general rule
followed by VPE. The advantages of this approach are believed to greatly outweigh
the minor incompatibilities.


Type specific behaviour
~~~~~~~~~~~~~~~~~~~~~~~

VPE knows which options consist of comma separated values, comma separated
characters or a sequence of character flags. You can use the '+=' and '-='
operators to add and remove values from such options. This only works for
attribute style option access.

.. code-block:: python

    # Make path = .,/usr/include
    vpe.vim.options.path = '.,/usr/include'

    # Make path = .,/usr/include,/usr/local/include,/usr/opt/include
    vpe.vim.options.path += '/usr/local/include,/usr/opt/include'

    # Remove two components leaving path = .,/usr/local/include
    vpe.vim.options.path -= '/usr/include,/usr/opt/include'

If the values within an option should not be repeated, VPE suppresses duplication.

.. code-block:: python

    vpe.vim.options.cpoptions = 'aAbBcDdg'
    vpe.vim.options.cpoptions += 'aAbJB'    # Just adds 'J', giving aAbBcDdgJ


Temporary option values
~~~~~~~~~~~~~~~~~~~~~~~

.. todo:: Move this section elsewhere.

It is quite common to need to temporarily change an option value in order to
perform some action. For example, to make sure an action will not fail because
a particular compatibility flag is set. VPE provides a context manager to do
this more cleanly.

.. code-block:: python

    with vpe.vim.temp_options() as options:
        options.report = 9999      # Prevent informational messages
        ...

    # Temporarily prevent informational messages
    with vpe.vim.temp_options(report=9999) as options:
        ...

    # Ensure full Vim compatibility.
    with vpe.vim.temp_options(cpoptions=vpe.VIM_DEFAULT) as options:
        ...

The last example shows how `VIM_DEFAULT` may be used to reset an option to its
default Vim value (like ``:set cpoptions&vim`` in vim script).


Vim vars and vvars
------------------

The `Vim.vvars` and `Vim.vars` properties allow Vim variables to be accessed as
attributes as well as using dictionary style lookup. In addition, it is
possible to set modifiable ``vvars`` using attribute access. The built in
module ``vvars`` object only allows reading of variables.


Vim registers
-------------

Vim's registers are made available by ``vpe.vim.registers``. This provides dictionary
like access for both reading and writing registers.

.. code-block:: python

    vpe.vim.registers['a']      # Access named register 'a'.
    vpe.vim.registers['2']      # Access register 2.
    vpe.vim.registers[2]        # Also access register 2.
    vpe.vim.registers['#']      # The alternate buffer name.


Access to Vim functions
-----------------------

The `vpe.vim` makes Vim's global functions available as methods.

.. code-block:: python

    int(vim.eval("col('.')"))   # Gives the current column, as an integer.

    vpe.vim.col('.')            # Does the same, but more simply.

This is much more convenient that using the ``vim``  module's ``eval`` function.

- The types of returned values are preserved (e.g. integer functions return integers),
  or converted to suitable Python types or wrapper class instances.

- Arguments are cleanly handled.

.. todo:: Needs better explanation.


Buffers, windows, tabpages, *etc*
---------------------------------

Where appropriate, other ``vim`` module attributes and methods are replaced by enhanced
VPE alternatives. For example ``vpe.vim.buffers`` provides a `Buffers` instance.

.. todo:: Needs better explanation.
