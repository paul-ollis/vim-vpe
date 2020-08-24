"""Pythonic access to the Vim commands.

This module provides functions for a majority of Vim's commands, which often
provide an easier approach to using :vim:`python-command`. For example:<py>:

    from vpe import commands
    commands.edit('README.txt')       # Start editing README.txt
    commands.print(a=10, b=20)        # Print lines 1 to 20
    commands.print(lrange=(10, 20))   # Print lines 1 to 20
    commands.write(bang=True)         # Same as :w!

Each command function is actually an instance of the `Command` class. See its
description for details of the arguments.

Most commands that can be entered at the colon prompt are supported. Structural
parts of vim-script (such as function, while, try, *etc*) are excluded.

The vpe, vpe.mapping and vpe.syntax modules provides some functions and
classes provide alternatives for some commands. You are encouraged to use these
alternatives in preference to the equivalent functions provided here. The
following is a summary of the alternatives.

`vpe.AutoCmdGroup`
    A replacement for augroup and autocmd.

`vpe.highlight`
    Provides keyword style arguments. See also the `vpe.syntax` module.
`vpe.error_msg`
    Writes a message with error highlightling, but does not raise a vim.error.
`vpe.mapping`
    This provides functions to make key mappings that are handled by Python
    functions.
`vpe.syntax`
    Provides a set of classes, functions and context managers to help define
    syntax highlighting.

See also: `vpe.pedit`.
"""

from vpe import common

_blockedVimCommands = set((
        "function",
        "endfunction",
        "if",
        "else",
        "elseif",
        "endif",
        "while",
        "endwhile",
        "continue",
        "break",
        "try",
        "endtry",
        "catch",
        "finally",
        "throw",
        "silent",
    ))


class Command:
    """Wrapper to invoke a Vim command as a function.

    Invocation takes the form of::

        func(arg[, arg[, arg...]], [bang=<flag>], [a=<start>], [b=<end>])
        func(arg[, arg[, arg...]], [bang=<flag>], [lrange=<range>])

    The command is invoked with the arguments separated by spaces. Each
    argument is formatted as by repr(). If the *bang* keyword argument is true
    then a '!' is appended to the command. A range of lines may be set using
    the *a* and *b* arguments or *lrange*. The *a* and *b* arguments are used
    in preference to the lrange argument. If only *b* is supplied then *a* is
    set to '.'.

    The *a* and *b* values may be strings or numbers. The *lrange*
    argument may be a string (*e.g.* '2,7',a vim.Range object, a standard
    Python range object or a tuple.

    :args:    All non-keyword arguments form plain arguments to the command.
    :bang:    If set then append '!' to the command.
    :lrange:  This may be a 2-tuple/list (specifying to (a, b)), a Python range
              object (specifying range(a - 1, b)) or a simple string range
              'a,b'. This argument is ignored if either *a* or *b* is provided.
    :a:       The start line.
    :b:       The end line (forming a range with *a*).
    :preview: For debugging. Do not execute the command, but return what would
              be passed to vim.command.
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, name):
        self.name = name

    def __call__(
            self, /, *args, bang=False, lrange='', a='', b='', preview=False):
        exclamation = '!' if bang else ''
        cmd = f'{self.name}{exclamation}'
        arg_expr = ''
        if args:
            arg_expr = ' ' + ' '.join(f'{arg}' for arg in args)
        range_expr = ''
        if not (a or b):
            if lrange:
                try:
                    range_expr = f'{lrange.start + 1},{lrange.stop} '
                except AttributeError:
                    if isinstance(lrange, (list, tuple)):
                        range_expr = f'{lrange[0]},{lrange[1]} '
                    else:
                        range_expr = f'{lrange} '
        else:
            if a and b:
                range_expr = f'{a},{b} '
            elif a:
                range_expr = f'{a} '
            else:
                range_expr = f'.,{b} '
        cmd = f'{range_expr}{cmd}{arg_expr}'
        if not preview:
            common.vim_command(cmd)
        return cmd


def __getattr__(name):
    if name.startswith('__'):
        raise AttributeError(
            f'No command function called {name!r} available')

    cname_form = f':{name}'
    if common.vim_eval(f'exists({cname_form!r})') == '2':
        if name not in _blockedVimCommands:
            return Command(name)

    raise AttributeError(
        f'No command function called {name!r} available')
