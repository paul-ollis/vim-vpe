=====================
VPE plug-in mechanism
=====================

Vim's default plug-in mechanism
===============================

Using Vim's standard mechanism for VPE based plug-ins is a bit fiddly because:

- You need a vim script file that then imports and initialises the actual
  Python code. Note that is it not a good idea to simply put all the code
  within 'python3 <<EOF ... EOF' because that will pollute Vim's global Python
  namespace.

- Such plug-ins depend on the VPE plug-in being loaded first.

So the Vim Python Extensions (VPE) provides a framework that simplifies writing
plug-ins in Python.


Plug-in structure
=================

A plug-in is basically Python module or package. In order to be recognised as a
VPE plug-in that should automatically be loaded, the module or package's
__init__.py must have docstring that starts with 'VPE-plugin: ' (note the space
after the colon). For example:

.. code-block:: py

    """VPE-plugin: Spam file support from within Vim."""

Triple, double quotes must be used and the docstring must start on line 1. If a
plug-in does not start like this then it is simply a library for other plug-in
code.

All VPE plug-ins are installed in::

    $HOME/.vim/pack/vpe_plugins          Unix
    $HOME/vimfiles/pack/vpe_plugins      Windows


Plug-in loading and initialisation
==================================

Loading
-------

VPE plug-ins are loaded after other Vim startup (by using the :vim:`VimEnter`
auto command). VPE scans the vpe_plugins directory for auto-loadable plug-in
modules and packages during normal Vim start up.

Each one it finds is loaded by simply importing it as a sub-module or
sub-pakage of the vpe_plugins package. For example if your plugin file is
my_plugin.py then VPE will import it as:

.. code-block:: py

    import vpe_plugins.my_plugin


Initialisation
--------------

Since a plug-in is imported, its top level code performs any necessary
initialisation. This will, of course, only be executed the first time it is
imported


Dependencies
------------

A plug-in can use code from other plug-in by simply importing its code. For example
my_plugin.py can use their_plugin.py by doing:

.. code-block:: py

    from vpe_plugins import their_plugin
