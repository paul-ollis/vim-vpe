Handling keys, events, etc.
===========================

Vim's scripting language provides several mechanisms to automatically respond
to various events, including.

- Special handling of key sequences (:vim:`map.txt`).
- User defined commands (:vim:`user-commands`).
- Auto commands events (:vim:`autocmd.txt`).
- Timer events (:vim:`timers`)
- Socket and pipe I/O (:vim:`channel.txt`).
- Buffer changes (:vim:`listener_add`)

All of these commonly involve either snippets of Vim script or references to
Vim functions that take specific arguments. This is obviously clean and pretty
easy using Vim script, but frankly quite tricky when you want (for example) to
map a key sequence to some Python code.

But it *can* be done.

VPE provides reasonably clean, Pythonic mechanisms, which are covered in the
following sections.

Timers are covered in the section :ref:`timers`.

.. toctree::
    :maxdepth: 2

    mapping.rst
    user-commands.rst
    auto-commands.rst
    channels.rst
    buf-changes.rst
