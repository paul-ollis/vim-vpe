==========
Change Log
==========

Version 0.7.3
-------------

- Prevent error when report Vim function invocation error.

- Prevent error when the VPE log window cannot be scrolled.


Version 0.7.2
-------------

- Commands created using the user_commands module now automatically have
  '--ehelp', '--lhelp' and '--phelp' options, which output help by plain
  printing, to the log or using a popup window. The '-h/--help' option's
  behaviour is now controlled by the 'Vpe help_mode' command.

- The VPE log now scrolls to the last line when it is gets shown in a buffer.
  Previously it did not scroll until some text was added.

- Clean up of the VPE API to remove some methods that should be private.

- Make the ``KeyHandler`` class accessible as ``vpe.KeyHandler``.

- The KeyHandler mix-in now automatically makes mappings global or buffer
  specific depending on the type of class.


Version 0.7.1
-------------

- Bug fix (#14). User commands broken for Python 12.8, 12.9 *etc.* and 13.1
  onwards.
