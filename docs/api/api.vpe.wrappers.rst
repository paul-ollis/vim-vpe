Module vpe.wrappers
===================


.. py:module:: wrappers

Wrappers around the built-in Vim Python types.

You should not normally need to import this module directly.

.. rubric:: Commands

.. py:class:: Commands(modifiers: dict[str, bool] = None)

    A namespace for the set of Vim commands.

    A single instance of this class is made available as `vpe.commands`.

    This class provides functions for a majority of Vim's commands, often
    providing a cleaner mechanism compared to :vim:`python-command`. For
    example:

    .. code-block:: py

        from vpe import commands
        commands.edit('README.txt')       # Start editing README.txt
        commands.print(a=10, b=20)        # Print lines 1 to 20
        commands.print(lrange=(10, 20))   # Print lines 1 to 20
        commands.write(bang=True)         # Same as :w!
        commands.split(vertical=True)     # Split current window vertically

    Each command function is actually an instance of the :py:obj:`Command`
    class. See its description for details of the arguments.

    Most commands that can be entered at the colon prompt are supported.
    Structural parts of vim-script (such as function, while, try, *etc*) are
    excluded.

    The vpe, vpe.mapping and vpe.syntax modules provides some functions and
    classes as alternatives for some commands. You are encouraged to use these
    alternatives in preference to the equivalent functions provided here. The
    following is a summary of the alternatives.

    `vpe.AutoCmdGroup`
        A replacement for augroup and autocmd.

    `vpe.highlight`
        Provides keyword style arguments. See also the `syntax` module.

    `vpe.error_msg`
        Writes a message with error highlighting, but does not raise a
        vim.error.

    `mapping`
        This provides functions to make key mappings that are handled by Python
        functions.

    `syntax`
        Provides a set of classes, functions and context managers to help
        define syntax highlighting.

    See also: `vpe.pedit`.

    **Parameters**

    .. container:: parameters itemdetails

        *modifiers*
            A dictionary of the default modifier flags for generated
            :py:obj:`Command` instances. This is only intended to be used by the
            `with_modifiers` class method.

    **Class methods**

        .. py:classmethod:: with_modifiers(**modifiers)

            Return a version of ``Commands`` that always applies modifiers.

            For example:

            .. code-block:: py

                silent = vpe.commands.modified(silent=True)
                silent.tabonly()

            Is equivalent to:

            .. code-block:: py

                vpe.commands.tabonly(silent=True)
