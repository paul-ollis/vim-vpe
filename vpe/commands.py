"""Pythonic access to the Vim commands."""

import vim as _vim

import vpe

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

    Invocation takes the form of:

        func(arg[, arg[, arg...]], [bang=<flag>], [a=<start>], [b=<end>])
        func(arg[, arg[, arg...]], [bang=<flag>], [range=<range>])

    The command is invoked with the arguments separated by spaces. Each
    argument is formatted as by repr(). If the ``bang`` keyword argument is
    true then a '!' is appended to the command. A range of lines may be set
    using the ``a`` and ``b`` arguments or ``range``. The ``a`` and ``b``
    arguments are used in preference to the range argument. If only ``b`` is
    supplied then ``a`` is set to '.'.

    The ``a`` and ``b`` values may be strings or numbers. The ``range``
    argument may be a string (*e.g.* '2,7',a vim.Range object or a standard
    Python range object.
    """

    def __init__(self, name):
        self.name = name

    def __call__ (
            self, /, *args,bang=False, range='', a='', b='', preview=False):
        exclamation = '!' if bang else ''
        cmd = f'{self.name}{exclamation}'
        arg_expr = ''
        if args:
            arg_expr = ' ' + ' '.join(f'{arg}' for arg in args)
        range_expr = ''
        if not (a or b):
            if range:
                try:
                    range_expr = f'{range.start + 1},{range.end + 1} '
                except AttributeError:
                    try:
                        range_expr = f'{range.start + 1},{range.stop} '
                    except AttributeError:
                        range_expr = f'{range} '
                print(f'{range_expr=}')
        else:
            if a and b:
                range_expr = f'{a},{b} '
            elif a:
                range_expr = f'{a} '
            else:
                range_expr = f'.,{b} '
        cmd = f'{range_expr}{cmd}{arg_expr}'
        if preview:
            return cmd
        else:
            vpe.vim_command(cmd)


def __getattr__(name):
    cname_form = f':{name}'
    if vpe.vim_eval(f'exists({cname_form!r})') == '2':
        if name not in _blockedVimCommands:
            return Command(name)

    raise AttributeError(
        f'No command funciton called {name!r} available')
