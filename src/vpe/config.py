"""Support for managing configuration information.

Configuration values are held as `config.Option` instances, which carry
additional meta-data such default values, valid ranges and descriptions.
Options prevent assignment of invalid values.

The `Config` class groups a set options together. It supports storage of option
values in an INI style configuration file and makes option values available as
(pseudo) instance attributes.
"""

import configparser
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import vpe

OptionValue = Union[int, str, bool]

CONFIG_SUBDIR = 'config.d'


class Option:
    """Details about a given option value.

    :@name:          The name of the value.
    :@default_value: A default value for the option.
    :@description:   A description for the value, used for help generation.
    """
    def __init__(self, name, default_value, *, description=''):
        self.name = name
        self.default_value = default_value
        self.description = description
        self._value = self._store_value = default_value

    @property
    def value(self):
        """"The current value for this option."""
        return self._value

    @property
    def store_value(self):
        """"The value for this option that will be store in the config file."""
        return self._store_value

    @property
    def store_repr(self):
        """"The representation of the `store_value`."""
        return str(self._store_value)

    def set(self, _value: OptionValue) -> str:               # pragma: no cover
        """Try to set this option's value.

        This needs to be over-ridden in subclasses.

        :return: A string describing why the attempt failed.
        """
        return f'Set not implemented for {self.__class__.__name__}'

    def copy_to_store(self):
        """Copy this value to the persistent layer."""
        self._store_value = self._value

    def simple_field_args(self) -> Dict[str, Any]:
        """Generate keyword arguments for a simple UI field.

        This may be extended in subclasses.
        """
        return {'prefix': self.name, 'description': self.description}

    @staticmethod
    def values() -> List[Any]:
        """Get the list of choices.

        This supports the protocol required for Tab completion support.
        """
        return []

    def __repr__(self):
        return str(self.value)


class String(Option):
    """A string value option."""

    def __init__(self, name, default_value='', *, description=''):
        super().__init__(name, default_value, description=description)

    def set(self, value: str) -> str:
        """Try to set this option's value."""
        self._value = value


class Bool(Option):
    """A boolean `config.Option`.

    Its value is always forced to be ``True`` or ``False``.
    """
    def __init__(self, name, default_value=False, *, description=''):
        super().__init__(name, default_value, description=description)

    def set(self, value: OptionValue) -> str:
        """Try to set this option's value.

        :return: A string describing why the attempt failed.
        """
        valid_names = {
            'true': True,
            'false': False,
            '1': True,
            '0': False}
        if isinstance(value, str):
            v = valid_names.get(value.strip().lower())
            if v is not None:
                self._value = v
                return ''
            return (f'Invalid value ({value!r}),'
                    f' valid are: {", ".join(valid_names)}')
        if isinstance(value, int):
            self._value = bool(value)
        return ''


class Choice(Option):
    """A `config.Option` that can take one of a set of values.

    :description:   A description for the value, used for help generation.
    :name:          The name of the value.
    :default_value: A default value for the option.
    :choices:       The set of allowed values.
    """
    def __init__(
            self, name, *, choices=(), default_value=None, description=''):
        assert choices
        if default_value is None:
            default_value = choices[0]
        else:
            assert default_value in choices
        super().__init__(name, default_value, description=description)
        self.choices = choices

    def set(self, value: OptionValue) -> str:
        """Try to set this option's value.

        :return: A string describing why the attempt failed.
        """
        if value not in self.choices:
            return f'{value!r} is not in permitted set of values'
        self._value = value
        return ''

    def values(self) -> List[Any]:
        """Get the list of choices.

        This supports the protocol required by a `Field`.
        """
        return self.choices

    def index(self) -> int:
        """Get the index for the current value."""
        return self.choices.index(self._value)


class Int(Option):                     # pylint: disable=too-few-public-methods
    """A `config.Option` that can take an integer value.

    :description:   A description for the value, used for help generation.
    :name:          The name of the value.
    :default_value: A default value for the option.
    :minval:        The minimum permitted value; ``None`` means unconstrained.
    :maxval:        The maximum permitted value; ``None`` means unconstrained.
    """
    def __init__(
            self, name, default_value=0, *,
            minval=None, maxval=None, description=''):
        super().__init__(name, default_value, description=description)
        self.minval = minval
        self.maxval = maxval

    def set(self, value: OptionValue) -> str:
        """Try to set this option's value.

        :return: A string describing why the attempt failed.
        """
        try:
            value = int(value)
        except ValueError:
            return f'{value!r} is not an integer'
        if self.minval is not None and value < self.minval:
            return f'{value} is less than {self.minval}'
        if self.maxval is not None and value > self.maxval:
            return f'{value} is greater than {self.maxval}'
        self._value = value
        return ''


class Config:
    """A collection of options forming a configuration.

    Each option's value is accessible as a pseudo attribute. All the methods of
    this class end with an underscore in order to prevent name clashes with
    options values.

    :@name:   The name of this configuration. By convention, for a plug-in,
              this is typically the plug-in's name.
    """
    def __init__(self, name: str):
        self._name = name
        self._options = {}

    def add_(self, option):
        """Add an option to this configuration.

        :option: The `config.Option` to add.
        """
        self._options[option.name] = option

    def get_(self, name):
        """Get the option with a given name.

        :raise KeyError: if the option does not exist.
        """
        return self._options[name]

    def load_(self):
        """Load options from an INI file.

        If, for example, `name` is 'omega' then (on Linux) the file
        ~/.vim/config.d/omega.ini will be loaded. Any existing option values
        not found in the file are left unchanged. Any value in the file that
        does not match a defined option is simply ignored.
        """
        path = Path(vpe.dot_vim_dir()) / f'{CONFIG_SUBDIR}/{self._name}.ini'
        try:
            f = open(path, 'rt', encoding='utf-8')
        except OSError:                                      # pragma: no cover
            vpe.error_msg(f'Could not read {path}.', soon=True)
            return
        parser = configparser.ConfigParser()
        try:
            parser.read_file(f)
        except configparser.Error:                           # pragma: no cover
            vpe.error_msg(f'Parse error for {path}.', soon=True)
            return
        for name, value in parser.defaults().items():
            if name in self._options:
                self._options[name].set(value)
                self._options[name].copy_to_store()

    def save_(self):
        """Save options to an INI file.

        If, for example, `name` is 'omega' then (on Linux) the file
        ~/.vim/config.d/omega.ini will be written. All previous contents of the
        file will be lost.
        """
        path = Path(vpe.dot_vim_dir()) / f'{CONFIG_SUBDIR}/{self._name}.ini'
        parent_dir = path.parent
        if not parent_dir.exists():
            try:
                path.parent.mkdir(parents=True)
            except OSError:                                  # pragma: no cover
                vpe.error_msg(
                    f'Could not create {path.parent} driectory.', soon=True)
                return
        try:
            f = open(path, 'wt', encoding='utf-8')
        except OSError:                                      # pragma: no cover
            vpe.error_msg(f'Could not write {path}.', soon=True)
            return
        parser = configparser.ConfigParser()
        for option in self._options.values():
            parser['DEFAULT'][option.name] = option.store_repr
        with f:
            parser.write(f)

    def ini_path_(self) -> Path:
        """Get the INI file path."""
        return Path(vpe.dot_vim_dir()) / f'{CONFIG_SUBDIR}/{self._name}.ini'

    def options_(self) -> Dict[str, Option]:
        """Get the dictionary of options."""
        return self._options

    def __getattr__(self, name) -> Optional[Any]:
        option = self._options.get(name)
        if option is None:
            raise AttributeError(f'Config object has no attribute {name!r}')
        return option.value
