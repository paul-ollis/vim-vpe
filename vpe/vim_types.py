"""A pseudo 'vim' types module.

This provides classes that represent underlying vim module classes. This is
only used to support type annotations.
"""


class vim_error(Exception):
    pass


class vim_buffer:
    pass


class vim_window:
    pass


class vim_tabpage:
    pass


class vim_options:
    pass


class vim_dictionary:
    pass


class vim_variables:
    pass
