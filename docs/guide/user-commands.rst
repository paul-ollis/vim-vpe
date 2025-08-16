=====================
User defined commands
=====================

.. |define_command| replace:: `vpe.define_command`
.. |CommandInfo| replace:: `vpe.CommandInfo`
.. |CommandHandler| replace:: `vpe.CommandHandler`
.. |command| replace:: `vpe.CommandHandler.command`


Defining commands
=================

VPE provides the |define_command| function as a way to create commands that
invoke Python functions or methods. In other words, you can define commands
that are implemented using Python functions (implementation functions). It maps
fairly closely to Vim's :vim:`:command`. Here is a very trivial example:

.. code-block:: python

    import vpe

    def echo_command(info: vpe.CommandInfo, *args):
        vpe.echo_msg(f'Echoing {args}')

    vpe.define_command('Echo', echo_command, nargs='*')

This creates a command call 'Echo', which takes an arbitrary number of
arguments. The 'echo_command' function receives these as positional parameters
following the initial |CommandInfo| argument. The command:

.. code-block:: vim

    Echo 1 2 three

will print::

    Echoing ('1', '2', 'Three')

.. For the above example, the command Echo hi paul me 'old mate' causes an
   error.

The |define_command| function takes a number of keyword arguments that are
analogues of the :vim:`:command` options with the same names.

nargs
    May be 0, 1, '\*', '?' or '+' ('0' and '1' as strings also work).

complete
    A string. Any value accepted by :vim:`:command`, except for 'custom' and
    'customlist'.

range
    Set to  ``True`` to simply allow the command to take a range. Use '%' to
    set a default range of the whole file and a number (may be as a string) to
    set a default count.

count
    The same as for :vim:`:command`, except that you can use integers or
    strings 'N'.

addr
    How special characters in a range are interpreted by Vim.

bang, bar, register, buffer
    Boolean values that act like the corresponding :vim:`:command` options.

The implementation of |define_command| invokes ``:command! ...`` so that any
previous command of the same name is replaced. The argument ``replace=False``
makes VPE invoke ``:command ...``.


CommandInfo
-----------

The |CommandInfo| argument makes it easy for the called function to determine
the details of how the command was invoked. It provides the following
attributes.

line1, line2
    The start line and end line of the command range.

range
    The number of items in the command range: 0, 1 or 2. This requires at least
    vim 8.0.1089; for earlier versions it is fixed as -1.

count
    Any count value supplied (see :vim:`command-count`).

bang
    True if the command was invoked with a '!'.

mods
    The command modifiers (see :vim:`:command-modifiers`). This is a space
    separated string.

reg
    The optional register, if provided.


Functions arguments
-------------------

Additional arguments can be passed to the command callback function. These are
defined using ``args`` and ``kwargs``.

.. code-block:: python

    def echo_command(info: vpe.CommandInfo, mode, *args, level=0):
        vpe.echo_msg(f'{mode}[{level}]: {args}')

    vpe.define_command(
        'Echo',
        echo_command,
        nargs='*',
        args=('info',),
        kwargs={'level': 2})

The command:

.. code-block:: vim

    Echo 20 30

Will print::

    info[2]: ('20', '30')

Notice that ``args`` preset using |define_command| are passed to the
implementation function *before* those of the ``Echo`` command.

The |CommandInfo| parameter can be suppressed if desired using the
``pass_info`` argument.

.. code-block:: python

    def echo_command(mode, *args, level=0):
        vpe.echo_msg(f'{mode}[{level}]: {args}')

    vpe.define_command(
        'Echo',
        echo_command,
        nargs='*',
        args=('info',),
        kwargs={'level': 2},
        pass_info=False)


Using decorators
================

.. note::

    This feature should be considered experimental at the moment. It will not
    be removed, but detailed behaviour, argument names, *etc.* may change in
    the next release.

In a similar way to key mapping, VPE provides a decorator approach to define
command implementation functions. The |CommandHandler| mixin class is used for
this.

.. code-block:: python

    class MessageGenerator(vpe.CommandHandler):
        command = vpe.CommandHandler.command

        def __init__(self):
            self.auto_define_commands()

        @command('Echo', nargs='*', args=('info',), kwargs={'level': 2})
        def echo_command(self, mode, *args, level=0):
            vpe.echo_msg(f'{mode}[{level}]: {args}')

    message_gen = MessageGenerator()

This can make code easier to read and maintain in some circumstances,
but it is not as flexible as |define_command|.

Note that the mappings are only created when the ``self.auto_define_commands()``
method is invoked.  Also note that, by default, the methods do not receive a
|CommandInfo| object as the first argument. Give the |command| decorator a
``pass_info=True`` argument to change this behaviour.

The |command| decorator accepts all the arguments of |define_command| except
for ``func``.
