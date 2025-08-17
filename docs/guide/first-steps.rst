Getting started
===============

.. |Commands| replace:: :py:obj:`Commands<wrappers.Commands>`
.. |vars| replace:: :py:obj:`vars<vpe.Vim.vars>`
.. |vvars| replace:: :py:obj:`vvars<vpe.Vim.vvars>`


.. _switching_from_vim:

Switching from the ``vim`` module
---------------------------------

If, as is quite likely, you have previously used Python for Vim scripting you
will be familiar with importing the ``vim`` module.

.. code-block:: python

    import vim

The ``vim`` module provides many features supporting interaction with the
executing Vim program. Detailed help is available - ``:help if_pyth.txt`` and
https://vimhelp.org/if_pyth.txt.html. The rest of this guide assumes that you
are reasonably familiar with this module.

In order to take advantage of VPE, a good starting point is to import ``vim``
from `vpe`.

.. code-block:: python

    from vpe import vim

.. sidebar:: Use of vpe.vim in examples.

    The style ``from vpe import vim`` is recommended. However, some examples
    and the text use ``vpe.vim`` in order to distinguish from the ``vim``
    module.

Then use this `vpe.vim` object instead of the ``vim`` module. The ``vim``
object provided by `vpe` is an instance of the `Vim` class, which is designed
to duplicate the module's behaviour almost exactly and provide significant
improvements. The next few sections introduce some of the important
enhancements.

The underlying ``vim`` module is accessible as ``vim.vim()``. This guide's text
and examples uses ``vim.vim()`` to make it clear when the standard ``vim``
module behaviour is being discussed.


Vim options
-----------

As well as accessing options using dictionary-like syntax, you can also access
options as attributes of ``vim.options``.

.. code-block:: python

    import vpe

    if vpe.vim.options['autoread']:  # Like vim.vim().options['autoread']
        ...

    if vpe.vim.options.autoread:     # Only works with vpe.vim.
        ...

Options can also be set this way.

.. code-block:: python

    vpe.vim.options.autoread = True

The attribute access provides a more Pythonic approach and provides some
advantages.


String conversion
~~~~~~~~~~~~~~~~~

VPE automatically converts option values to strings, which greatly simplifies a
lot of code.

.. code-block:: python

    import vim
    import vpe

    vim.options['keywordprg']             # b'man -s', not a Python string!

    vpe.vim.options['keywordprg']         # 'man -s'
    vpe.vim.options.keywordprg            # 'man -s'

The conversion is performed assuming that the byte value is encoded as UTF-8.
Decoding errors are ignored.

Note that this is one example where the `Vim` class chooses to behave slightly
differently to the ``vim`` module. Sensible, automatic conversion between bytes
and strings is a general rule followed by VPE. The advantages of this approach
are considered to outweigh the minor incompatibilities.


Type specific behaviour
~~~~~~~~~~~~~~~~~~~~~~~

VPE knows which options consist of comma separated values, comma separated
characters or a sequence of character flags. You can use the '+=' and '-='
operators to add and remove values from such options. This only works for
attribute style option access.

.. code-block:: python

    # Set path = .,/usr/include
    vpe.vim.options.path = '.,/usr/include'

    # Set path = .,/usr/include,/usr/local/include,/usr/opt/include
    vpe.vim.options.path += '/usr/local/include,/usr/opt/include'

    # Remove two components leaving path = .,/usr/local/include
    vpe.vim.options.path -= '/usr/include,/usr/opt/include'

If the values within an option should not be repeated, VPE automatically
suppresses duplication.

.. code-block:: python

    vpe.vim.options.cpoptions = 'aAbBcDdg'
    vpe.vim.options.cpoptions += 'aAbJB'    # Just adds 'J', giving aAbBcDdgJ


Temporary option values
~~~~~~~~~~~~~~~~~~~~~~~

It is quite common to need to temporarily change an option value in order to
perform some action. For example, to make sure an action will not fail because
a particular compatibility flag is not set. VPE provides a context manager to
do this more cleanly.

.. code-block:: python

    with vpe.vim.temp_options() as options:
        # Prevent informational messages while this context is active.
        options.report = 9999
        ...

    # Another way to temporarily prevent informational messages
    with vpe.vim.temp_options(report=9999):
        ...

    # Ensure full Vim compatibility.
    with vpe.vim.temp_options(cpoptions=vpe.VIM_DEFAULT) as options:
        ...

The last example shows how `VIM_DEFAULT` may be used to reset an option to its
default Vim value (like ``:set cpoptions&vim`` in vim script).


Vim vars and vvars
------------------

The |vvars| and |vars| properties allow Vim variables to be accessed as
attributes in addition to dictionary style lookup. In addition, it is possible
to set modifiable ``vvars`` using attribute access. The built in module
``vvars`` object only allows reading of variables.


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

Vim's global functions are available as methods.

.. code-block:: python

    n = int(vim.eval("col('.')"))   # Gives the current column, as an integer.

    n = vpe.vim.col('.')            # Does the same, but more simply.

This is much more convenient that using the ``vim``  module's ``eval``
function, supporting much more Pythonic code.

Vim functions invoked via ``vpe.vim`` methods return suitable Python types.
This is similar to invoking function via ``vim.vpe().Function``
(:vim:`python-funcion`), but VPE's type conversion is more extensive.

If a exception occurs when the function is invoked, VPE logs fairly detailed
information about the function call.

Functions provided by the standard ``vim`` module take precedence. So
``vpe.vim.eval`` refers to the eval function in Vim's ``vim`` module
(:vim:`python-eval`) not Vim's ``eval`` function (:vim:`eval()`).


Buffers, windows, tabpages, *etc*
---------------------------------

Where appropriate, various other ``vim`` module attributes and methods are
replaced by enhanced VPE alternatives. For example:

.. code-block:: python

    import vpe

    buffers = vpe.vim.buffers   # The vpe.Buffers object.
    b = buffers[1]              # A vpe.Buffer object.

In some cases the VPE substituted object is just a very thin wrapper around the
underling ``vim`` module object. For example, the `vpe.Buffers` object does not
add any methods, but it supplies `vpe.Buffer` objects which *do* provide
enhanced features.


Commands as functions
---------------------

VPE provides a `commands` object that makes Vim's commands available as
methods. This is typically much easier and more Pythonic that using
``vim.command``.

.. code-block:: python

    from vpe import commands

    # This is equivalent to vim.command('edit myfile.py')
    commands.edit('myfile.py')

Executing commands this way makes it much easier to use non-strings, values
stored in variables and avoids many cases where ``vim.command`` required
special characters to be escaped.

The `commands` methods provide mechanisms to support other features of Vim
commands, such as adding a '!'. See |Commands| for details.

The Vim commands that are really just part of the Vim scripting language
(``if``, ``try``, ``throw``, *etc.* are not exposed as commands methods.
