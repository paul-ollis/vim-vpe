"""Python support for key sequence mapping.

This module provides support for mapping key sequences to Python function
calls.
"""

import collections

from vpe import vim, MapCallback
from vpe import log, commands

_sw_normal = '<c-\\><c-n>'

mode_to_map_command = {
    'normal': 'nnoremap',
    'visual': 'xnoremap',
    'select': 'snoremap',
    'op-pending': 'onoremap',
    'insert': 'inoremap',
    # Not supported unless (and until) a valid use-case presents itself.
    # 'command':    cnoremap,
}


# Special args to consider.
#   script  - Probably not useful.
#   expr    - Probably should have a different function.
def map(
        mode, keys, func, buffer=True, silent=True, unique=False, nowait=False,
        args=(), kwargs={}):
    """Set up a normal mapping that invokes a Python function.

    :param mode:
        A string defining the mode in which the mapping occurs. This should be
        one of: normal, visual, select, op-pending, insert, command.
    :param keys:
        The key sequence to be mapped.
    :param func:
        The Python function to invoke for the mapping.
    :param buffer:
        Use the <buffer> special argument. Defaults to True.
    :param silent:
        Use the <silent> special argument. Defaults to True.
    :param unique:
        Use the <unique> special argument. Defaults to False.
    :param nowait:
        Use the <nowait> special argument. Defaults to False.
    :param args:
        Additional arguments to pass to the mapped function.
    :param kwargs:
        Additional keyword arguments to pass to the mapped function.
    """
    mapinfo = mode, keys
    cb = MapCallback(func, info=mapinfo, py_args=args, py_kwargs=kwargs)
    specials = [el for el in [
        '<buffer>' if buffer else '',
        '<silent>' if silent else '',
        '<unique>' if unique else '',
        '<nowait>' if unique else '',
    ] if el]
    map_cmd = mode_to_map_command[mode]
    if mode == 'normal':
        rhs = f':silent {cb.as_call()}<CR>'
    elif mode == 'insert':
        rhs = f'<C-R>={cb.as_invocation()}<CR>'
    elif mode == 'visual':
        rhs = f':<C-U>silent {cb.as_call()}<CR>'
    elif mode == 'select':
        rhs = f':<C-U>silent {cb.as_call()}<CR>'
    elif mode == 'op-pending':
        rhs = f':<C-U>silent {cb.as_call()}<CR>'
    else:
        raise NotImplementedError

    cmd = f'{map_cmd} <special> {" ".join(specials)} {keys} {rhs}'

    log(cmd)
    vim.command(cmd)


def fred(mapinfo, *args, **kwargs):
    log.clear()
    log(mapinfo, args, kwargs, vim.current.window.cursor)
    m = mapinfo
    log(f'{m.start_cursor=}')
    log(f'{m.end_cursor=}')
    log(f'{m.vmode=}')
    log(f'{m.line_range=}')
    return ''


# Hello 0:messagepaul
log.clear()
log.show()
map('normal', '<F3>', fred, args=(99,), kwargs={'a': 10})
map('insert', '<F3>', fred, args=(88,), kwargs={'a': 10})
map('visual', '<F3>', fred, args=(88,), kwargs={'a': 10})
map('select', '<F3>', fred, args=(88,), kwargs={'a': 10})
map('op-pending', '<F3>', fred, args=(88,), kwargs={'a': 10})
