==========
Change Log
==========

Version 0.7.3
-------------

- Enhance the Buffer class's support for properties.

  - Can now set single lines marked up using Rich-like styling.

  - Can use regular expressions to apply Rich-like styling to text strings.

  - Buffer methods that set properties handle multi-byte Unicode code points.
    Unlike with direct use of the Vim ``prop_...()`` functions you do not need
    to explicitly convert from character to byte offsets.

  - Added methods that provide nice wrapping for several Vim ``prop_...()``
    functions:

    1. clear_line_props. Clear properties for a single line (uses prop_clear).

    2. remove_line_props. Selectively remove properties from a single line
       (uses prop_remove).

    3. query_props. Effectively a wrapper for prop_list for the buffer.

    4. add_line_props. Like existing set_line_prop, but can set multiple properties.

    The add_line_prop and add_line_props can take an ID argument, which is useful
    with the remove_line_props method.

- Provide explicit update method for wrapped Vim dictionaries.

- Provide toggle method for Log to toggle display in a buffer.

- Prevent error when report Vim function invocation error.

- Prevent error when the VPE log window cannot be scrolled.

- Correct key mapping clean up.

- Support new unbuffered option for listener_add.

  Buffered mode is the default, but unbuffered mode can be used if the Vim
  version is new enough.


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
