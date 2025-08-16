=====================
VPE plug-in mechanism
=====================

Vim's default plug-in mechanism
===============================

Using Vim's standard mechanism for VPE based plug-ins is a bit fiddly because:

- You need a vim script file that then imports and initialises the actual
  Python code. Note that is it not a good idea to simply put all the code
  within a ``python3 <<EOF ... EOF`` construct because that will pollute Vim's
  Python namespace, making it difficult for plug-ins to coexist.

- Such plug-ins depend on the VPE plug-in being loaded first.

So VPE provides its own framework that simplifies writing plug-ins in Python
that rely on VPE.


Plug-in structure
=================

A plug-in is basically a Python module or package. In order to be recognised as
a VPE plug-in that should automatically be loaded, the module or package's
__init__.py must have docstring that starts with 'VPE-plugin: ' (note the space
after the colon). For example:

.. code-block:: py

    """VPE-plugin: Spam support from within Vim."""

Triple, double quotes (""") must be used and the docstring must start on line
one. If a module or package does not conform to these requirements then it
simply acts as a library for other plug-in code.

All VPE plug-ins are installed in::

    $HOME/.vim/pack/vpe_plugins          Unix
    $HOME/vimfiles/pack/vpe_plugins      Windows


Plug-in loading and initialisation
==================================

Loading
-------

VPE plug-ins are loaded after Vim completes it normal startup an plug-in loading
(by using the :vim:`VimEnter` auto command).

VPE scans the vpe_plugins directory for auto-loadable plug-in modules and
packages. Each plug-in found is loaded by simply importing it as a sub-module
or sub-package of the ``vpe_plugins`` namespace package. For example if your plugin
file is my_plugin.py then VPE will effectively import it as:

.. code-block:: py

    import vpe_plugins.my_plugin

VPE imports plug-ins in ``sorted()`` order. This should be considered as an
implementation detail, that can sometimes make debugging plug-ins easier. This
feature should not be relied on by normal plug-in code. A future version of
VPE may change to a different, but still consistent, import order.


Initialisation
--------------

Since a plug-in is imported, its top level code performs any necessary
initialisation. This will, of course, only be executed the first time it is
imported

If a plug-in is not able to load properly, for example because a required third
party Python library is missing, then it can raise the `vpe.Finish` exception to
abort loading and provide some details. For example::

.. code-block:: py

    import vpe

    try:
        import spam
    except ImportError:
        raise vpe.Finish('Could not import the required "spam" module.')

The failure will be reported in the VPE log.


Dependencies
------------

A plug-in can use code from another plug-in by simply importing its code. For
example my_plugin.py can use their_plugin.py by doing:

.. code-block:: py

    from vpe_plugins import their_plugin
