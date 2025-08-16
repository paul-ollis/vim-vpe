Module vpe.config
=================


.. py:module:: config

Support for managing configuration information.

Configuration values are held as `config.Option` instances, which carry
additional meta-data such default values, valid ranges and descriptions.
Options prevent assignment of invalid values.

The `Config` class groups a set options together. It supports storage of option
values in an INI style configuration file and makes option values available as
(pseudo) instance attributes.

.. rubric:: Bool

.. py:class:: Bool(name,default_value=False,description='')

    A boolean `config.Option`.

    Its value is always forced to be ``True`` or ``False``.

    **Methods**

        .. py:method:: set(value: Union[int, str, bool]) -> str

            Try to set this option's value.


            **Return value**

            .. container:: returnvalue itemdetails

                A string describing why the attempt failed.

.. rubric:: Choice

.. py:class:: Choice(name,choices=(),default_value=None,description='')

    A `config.Option` that can take one of a set of values.


    **Parameters**

    .. container:: parameters itemdetails

        *description*
            A description for the value, used for help generation.
        *name*
            The name of the value.
        *default_value*
            A default value for the option.
        *choices*
            The set of allowed values.

    **Methods**

        .. py:method:: index() -> int

            Get the index for the current value.

        .. py:method:: set(value: Union[int, str, bool]) -> str

            Try to set this option's value.


            **Return value**

            .. container:: returnvalue itemdetails

                A string describing why the attempt failed.

        .. py:method:: values() -> List[Any]

            Get the list of choices.

            This supports the protocol required by a `Field`.

.. rubric:: Config

.. py:class:: Config(name: str)

    A collection of options forming a configuration.

    Each option's value is accessible as a pseudo attribute. All the methods of
    this class end with an underscore in order to prevent name clashes with
    options values.

    **Parameters**

    .. container:: parameters itemdetails

        *name*
            The name of this configuration. By convention, for a plug-in,
            this is typically the plug-in's name.

    **Attributes**

        .. py:attribute:: name

            The name of this configuration. By convention, for a plug-in,
            this is typically the plug-in's name.

    **Methods**

        .. py:method:: add_(option)

            Add an option to this configuration.


            **Parameters**

            .. container:: parameters itemdetails

                *option*
                    The `config.Option` to add.

        .. py:method:: get_(name)

            Get the option with a given name.


            **Exceptions raised**

            .. container:: exceptions itemdetails

                *KeyError*
                    if the option does not exist.

        .. py:method:: ini_path_() -> pathlib.Path

            Get the INI file path.

        .. py:method:: load_()

            Load options from an INI file.

            If, for example, `name` is 'omega' then (on Linux) the file
            ~/.vim/config.d/omega.ini will be loaded. Any existing option values
            not found in the file are left unchanged. Any value in the file that
            does not match a defined option is simply ignored.

        .. py:method:: options_() -> Dict[str, vpe.config.Option]

            Get the dictionary of options.

        .. py:method:: save_()

            Save options to an INI file.

            If, for example, `name` is 'omega' then (on Linux) the file
            ~/.vim/config.d/omega.ini will be written. All previous contents of the
            file will be lost.

.. rubric:: Int

.. py:class:: Int(...)

    .. code::

        Int(
                name,
                default_value=0,
                minval=None,
                maxval=None,

    A `config.Option` that can take an integer value.


    **Parameters**

    .. container:: parameters itemdetails

        *description*
            A description for the value, used for help generation.
        *name*
            The name of the value.
        *default_value*
            A default value for the option.
        *minval*
            The minimum permitted value; ``None`` means unconstrained.
        *maxval*
            The maximum permitted value; ``None`` means unconstrained.

    **Methods**

        .. py:method:: set(value: Union[int, str, bool]) -> str

            Try to set this option's value.


            **Return value**

            .. container:: returnvalue itemdetails

                A string describing why the attempt failed.

.. rubric:: Option

.. py:class:: Option(name,default_value,description='')

    Details about a given option value.


    **Parameters**

    .. container:: parameters itemdetails

        *name*
            The name of the value.
        *default_value*
            A default value for the option.
        *description*
            A description for the value, used for help generation.

    **Attributes**

        .. py:attribute:: default_value

            A default value for the option.

        .. py:attribute:: description

            A description for the value, used for help generation.

        .. py:attribute:: name

            The name of the value.

    **Properties**

        .. py:property:: store_repr()

            "The representation of the `store_value`.

        .. py:property:: store_value()

            "The value for this option that will be store in the config file.

        .. py:property:: value()

            "The current value for this option.

    **Methods**

        .. py:method:: copy_to_store()

            Copy this value to the persistent layer.

        .. py:method:: set(_value: Union[int, str, bool]) -> str

            Try to set this option's value.

            This needs to be over-ridden in subclasses.

            **Return value**

            .. container:: returnvalue itemdetails

                A string describing why the attempt failed.

        .. py:method:: simple_field_args() -> Dict[str, Any]

            Generate keyword arguments for a simple UI field.

            This may be extended in subclasses.

    **Static methods**

        .. py:staticmethod:: values() -> List[Any]

            Get the list of choices.

            This supports the protocol required for Tab completion support.

.. rubric:: String

.. py:class:: String(name,default_value='',description='')

    A string value option.

    **Methods**

        .. py:method:: set(value: str) -> str

            Try to set this option's value.
