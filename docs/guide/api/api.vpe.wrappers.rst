Module vpe.wrappers
===================

.. py:module:: vpe.wrappers

Wrappers around the built-in Vim Python types.

You should not normally need to import this module directly.

Command
-------

.. py:class:: vpe.wrappers.Command(name)

    Wrapper to invoke a Vim command as a function.

    The `Commands` creates instances of this; direct instantiation by users is
    not intended.

    Invocation takes the form of:

    ::

        func(arg[, arg[, arg...]], [bang=<flag>], [a=<start>], [b=<end>],
             [modifiers])
        func(arg[, arg[, arg...]], [bang=<flag>], [lrange=<range>],
             [modifiers])

    The command is invoked with the arguments separated by spaces. Each
    argument is formatted as by repr(). If the *bang* keyword argument is true
    then a '!' is appended to the command. A range of lines may be set using
    the *a* and *b* arguments or *lrange*. The *a* and *b* arguments are used
    in preference to the lrange argument. If only *b* is supplied then *a* is
    set to '.' (the current line). Additional *modifiers* keyword arguments,
    such as 'vertical' are also supported; see details below.

    The *a* and *b* values may be strings or numbers. The *lrange*
    argument may be a string (*e.g.* '2,7',a vim.Range object, a standard
    Python range object or a tuple.

    **Parameters**

    .. container:: parameters itemdetails

        *args*
            All non-keyword arguments form plain arguments to the command.
        *bang*
            If set then append '!' to the command.
        *lrange*
            This may be a 2-tuple/list (specifying to (a, b)), a Python
            range object (specifying range(a - 1, b)) or a simple string
            range 'a,b'. This argument is ignored if either *a* or *b* is
            provided.
        *a*
            The start line.
        *b*
            The end line (forming a range with *a*).
        *vertical*
            Run with the vertical command modifier.
        *aboveleft*
            Run with the aboveleft command modifier.
        *belowright*
            Run with the belowright command modifier.
        *topleft*
            Run with the topleft command modifier.
        *botright*
            Run with the botright command modifier.
        *keepalt*
            Run with the keepalt command modifier. Default = True.
        *preview*
            For debugging. Do not execute the command, but return what
            would be passed to vim.command.

Commands
--------

.. py:class:: vpe.wrappers.Commands

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

    Each command function is actually an instance of the `Command` class. See
    its description for details of the arguments.

    Most commands that can be entered at the colon prompt are supported.
    Structural parts of vim-script (such as function, while, try, *etc*) are
    excluded.

    The vpe, vpe.mapping and vpe.syntax modules provides some functions and
    classes provide alternatives for some commands. You are encouraged to use
    these alternatives in preference to the equivalent functions provided here.
    The following is a summary of the alternatives.

    `vpe.AutoCmdGroup`
        A replacement for augroup and autocmd.

    `vpe.highlight`
        Provides keyword style arguments. See also the `vpe.syntax` module.
    `vpe.error_msg`
        Writes a message with error highlightling, but does not raise a
        vim.error.
    `vpe.mapping`
        This provides functions to make key mappings that are handled by Python
        functions.
    `vpe.syntax`
        Provides a set of classes, functions and context managers to help
        define syntax highlighting.

    See also: `vpe.pedit`.