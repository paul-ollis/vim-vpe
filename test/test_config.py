"""Tests for the VPE configuration support."""

# pylint: disable=unused-wildcard-import,wildcard-import
# pylint: disable=deprecated-method
# pylint: disable=wrong-import-order

import os
import shutil
from pathlib import Path

from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import runModule, test

import support

from vpe import config

_run_after = ['test_vim.py']


class BoolOption(support.Base):
    """The VPE config.Bool option.

    Bool is a very simple derivation of the Option base class.
    """
    @test(testID='conf-bool')
    def bool_option_init(self):
        """A Bool option requires a name and default value.

        The name and default value are available as attributes.
        """
        bopt = config.Bool('test_bool', False)
        failUnlessEqual('test_bool', bopt.name)
        failUnless(bopt.default_value is False)
        bopt = config.Bool('test_bool', True)
        failUnless(bopt.default_value is True)

    @test(testID='conf-bool-set')
    def bool_option_set(self):
        """A Bool option's current value can be modified.

        The current value is available as the value property. Support for repr
        is provided.
        """
        bopt = config.Bool('test_bool', False)
        failUnless(bopt.value is False)
        ret = bopt.set(True)
        failUnless(bopt.default_value is False)
        failUnless(bopt.value is True)
        failUnlessEqual('', ret)

        failUnlessEqual('True', repr(bopt))
        failUnlessEqual('True', str(bopt))

    @test(testID='conf-bool-set-str')
    def bool_option_set_str(self):
        """A Bool option's value can be set using strings True and False.

        This makes setting from a configuration file easier. Spaces are
        stripped and the case is important.
        """
        bopt = config.Bool('test_bool', False)
        ret = bopt.set(' True ')
        failUnless(bopt.value is True)
        failUnlessEqual('', ret)
        ret = bopt.set(' false ')
        failUnless(bopt.value is False)
        failUnlessEqual('', ret)

    @test(testID='conf-bool-set-fail')
    def bool_option_set_fail(self):
        """Failure to set a bool option returns an explanatory message."""
        bopt = config.Bool('test_bool', False)
        message = bopt.set('wibble')
        failIf(bopt.value is True)
        failUnlessEqual(
            "Invalid value ('wibble'), valid are: true, false, 1, 0", message)

    @test(testID='conf-bool-descr')
    def bool_option_descr(self):
        """A Bool option can be given a descripion.

        Multi-line descriptions are encouraged. The description attribute
        holds the text, including newlines and leading whitespace.
        """
        bopt = config.Bool(
            'test_bool', False, description='''
            This is a test configuration item.
            It is truthy.
        ''')
        failUnlessEqual('test_bool', bopt.name)
        failUnlessEqual(
            '\n            This is a test configuration item.\n'
            '            It is truthy.\n        ',
            bopt.description)

    @test(testID='conf-bool-field-support')
    def bool_option_supports_ui_fields(self):
        """A Bool option provides support for UI fields.

        This helps support the UI configuration panel.
        """
        bopt = config.Bool(
            'test_bool', False, description='A bool option')
        kwargs = bopt.simple_field_args()
        failUnlessEqual('test_bool', kwargs['prefix'])
        failUnlessEqual('A bool option', kwargs['description'])
        failUnlessEqual([], bopt.values())


class ChoiceOption(support.Base):
    """The VPE config.Choice option.

    This holds a string that is constrained to be one of a fixed set of values.
    """
    @test(testID='conf-choice')
    def choice_option_init(self):
        """A Choice option requires a name and sequence of choices.

        The name and choices value are available as attributes. The default
        value is the first choice.
        """
        copt = config.Choice('test_choice', choices=('one', 'two', 'three'))
        failUnlessEqual('test_choice', copt.name)
        failUnlessEqual('one', copt.default_value)
        failUnlessEqual(('one', 'two', 'three'), copt.choices)

    @test(testID='conf-choice-min-1-value')
    def choice_requires_1_value(self):
        """At least one value must be supplied for the set of choces."""
        failUnlessRaises(
            AssertionError, config.Choice, 'test_choice', choices=())

    @test(testID='conf-choice-default')
    def choice_option_default(self):
        """An explicit default value can be provided."""
        copt = config.Choice(
            'test_choice', choices=('one', 'two', 'three'),
            default_value='two')
        failUnlessEqual('test_choice', copt.name)
        failUnlessEqual('two', copt.default_value)

    @test(testID='conf-choice-default-invalid')
    def choice_option_default_invalid(self):
        """The default must be a valid choice."""
        failUnlessRaises(
            AssertionError, config.Choice, 'test_choice',
            choices=('one', 'two', 'three'),
            default_value='four')

    @test(testID='conf-choice-set')
    def choice_option_set(self):
        """A Choice option's current value can be modified.

        The current value is available as the value property. Support for repr
        is provided.
        """
        copt = config.Choice('test_choice', choices=('one', 'two', 'three'))
        failUnlessEqual('one', copt.value)
        ret = copt.set('two')
        failUnlessEqual('one', copt.default_value)
        failUnlessEqual('two', copt.value)
        failUnlessEqual('', ret)

        failUnlessEqual('two', repr(copt))
        failUnlessEqual('two', str(copt))

    @test(testID='conf-choice-set-fail')
    def choice_option_set_fail(self):
        """Failure to set a choice option returns an explanatory message."""
        copt = config.Choice('test_choice', choices=('one', 'two', 'three'))
        message = copt.set('four')
        failUnlessEqual('one', copt.value)
        failUnlessEqual("'four' is not in permitted set of values", message)

    @test(testID='conf-choice-field-support')
    def bool_option_descr(self):
        """A Choice option provides support for UI fields.

        This helps support the UI configuration panel.
        """
        copt = config.Choice('test_choice', choices=('one', 'two', 'three'))
        failUnlessEqual(('one', 'two', 'three'), copt.values())


class IntOption(support.Base):
    """The VPE config.Int option.

    This holds a integer that may be constrained to a range of values.
    """
    @test(testID='conf-int')
    def int_option_init(self):
        """A Int option requires a name and default value.

        The name and ints value are available as attributes. The default
        value is the first int.
        """
        iopt = config.Int('test_int', 2)
        failUnlessEqual('test_int', iopt.name)
        failUnlessEqual(2, iopt.default_value)

    @test(testID='conf-int-set')
    def int_option_set(self):
        """A Int option's current value can be modified.

        The current value is available as the value property. Support for repr
        is provided.
        """
        iopt = config.Int('test_int', 2)
        failUnlessEqual(2, iopt.value)
        iopt.set(-987654321)
        failUnlessEqual(-987654321, iopt.value)

        failUnlessEqual('-987654321', repr(iopt))
        failUnlessEqual('-987654321', str(iopt))

    @test(testID='conf-int-set-fail')
    def int_option_set_fail(self):
        """Failure to set a int option returns an explanatory message.

        The typical failure is for an out of range value.
        """
        iopt = config.Int('test_int', 2, minval=-1, maxval=10)
        message = iopt.set(-2)
        failUnlessEqual(2, iopt.value)
        failUnlessEqual("-2 is less than -1", message)

    @test(testID='conf-int-set-bad-type')
    def int_option_set_bad_type(self):
        """Set will fail if the type is invalid."""
        iopt = config.Int('test_int', 2)
        message = iopt.set('hello')
        failUnlessEqual(2, iopt.value)
        failUnlessEqual("'hello' is not an integer", message)

    @test(testID='conf-int-set-str-conv')
    def int_option_set_from_string(self):
        """Set will accept the string representation of an int."""
        iopt = config.Int('test_int', 2)
        message = iopt.set('99')
        failUnlessEqual(99, iopt.value)
        failUnlessEqual("", message)

    @test(testID='conf-int-indepent-limits')
    def int_option_independent_limits(self):
        """The min and max values can be independently set or omitted.

        When omitted then no min/max restriction is applied.
        """
        iopt = config.Int('test_int', 2, maxval=10)
        message = iopt.set(-2)
        failUnlessEqual(-2, iopt.value)
        failUnlessEqual("", message)

        message = iopt.set(11)
        failUnlessEqual(-2, iopt.value)
        failUnlessEqual("11 is greater than 10", message)


class StringOption(support.Base):
    """The VPE config.String option.

    This simply holds a string.
    """
    @test(testID='conf-string')
    def stringe_option_init(self):
        """A String option requires a name and optiional default value."""
        sopt = config.String('test_string', default_value='Hi')
        failUnlessEqual('test_string', sopt.name)
        failUnlessEqual('Hi', sopt.default_value)
        failUnlessEqual('Hi', sopt.value)

    @test(testID='conf-string-set')
    def stringe_option_set(self):
        """A String can bet set."""
        sopt = config.String('test_string', default_value='Hi')
        failUnlessEqual('Hi', sopt.value)
        sopt.set('modified')
        failUnlessEqual('modified', sopt.value)


class ConfigSupport(support.Base):
    """The VPE config.Config class.

    This holds a set of config options. The values can be read from and saved
    to a file.
    """
    @test(testID='conf-store')
    def config_create(self):
        """A Config object is created with a given name.

        The name is used to construct the name of the INI file used to store
        persistent values.
        """
        conf = config.Config('test_conf')
        home = Path(__file__).resolve().parent / 'rt_test_data'
        conf_path = home / '.vim/config.d/test_conf.ini'
        failUnlessEqual(conf_path, conf.ini_path_())

    @test(testID='conf-store-add')
    def config_add(self):
        """Options are added using the add_() method.

        Option values appear as attributes of the Config object.
        """
        conf = config.Config('test_conf')
        bopt = config.Bool('test_bool', True)
        copt = config.Choice('test_choice', choices=('one', 'two', 'three'))
        iopt = config.Int('test_int', 2)
        conf.add_(bopt)
        conf.add_(copt)
        conf.add_(iopt)

        failUnless(conf.test_bool is True)
        failUnlessEqual('one', conf.test_choice)
        failUnlessEqual(2, conf.test_int)

    @test(testID='conf-get')
    def config_get(self):
        """Options can be accessed using the get method.

        Option values appear as attributes of the Config object.
        """
        conf = config.Config('test_conf')
        bopt = config.Bool('test_bool', True)
        copt = config.Choice('test_choice', choices=('one', 'two', 'three'))
        iopt = config.Int('test_int', 2)
        conf.add_(bopt)
        conf.add_(copt)
        conf.add_(iopt)

        failUnless(conf.get_('test_bool').value is True)
        failUnlessEqual('one', conf.get_('test_choice').value)
        failUnlessEqual(2, conf.get_('test_int').value)

    @test(testID='conf-save-load')
    def config_save_load(self):
        """The config can be saved and loaded.

        The config.d directory is created as required.
        """
        conf = config.Config('test_conf')
        bopt = config.Bool('test_bool', True)
        copt = config.Choice('test_choice', choices=('one', 'two', 'three'))
        iopt = config.Int('test_int', 2)
        conf.add_(bopt)
        conf.add_(copt)
        conf.add_(iopt)

        home = Path(__file__).resolve().parent / 'rt_test_data'
        config_d = home / '.vim/config.d'
        if config_d.exists():
            try:
                shutil.rmtree(config_d)
            except OSError:
                # I do not understand, but running under Cygwin I have seen
                # PermissionError raised when shtil.rmtree tries
                # os.rmdir(config_d). Yet the following succeeds!
                os.rmdir(config_d)

        conf.save_()
        bopt.set(False)
        iopt.set(99)
        copt.set('three')
        failUnless(conf.test_bool is False)
        failUnlessEqual('three', conf.test_choice)
        failUnlessEqual(99, conf.test_int)

        conf.load_()
        failUnless(conf.test_bool is True)
        failUnlessEqual('one', conf.test_choice)
        failUnlessEqual(2, conf.test_int)

    @test(testID='conf-attr-error')
    def missing_config_name(self):
        """It is an attribute error if a config value cannot be found."""
        conf = config.Config('test_conf')
        failUnlessRaises(AttributeError, getattr, conf, 'wibble')

    @test(testID='conf-get_options')
    def config_get_options(self):
        """The options_ method provides access to the underlying dict."""
        conf = config.Config('test_conf')
        bopt = config.Bool('test_bool', True)
        copt = config.Choice('test_choice', choices=('one', 'two', 'three'))
        iopt = config.Int('test_int', 2)
        conf.add_(bopt)
        conf.add_(copt)
        conf.add_(iopt)

        result = conf.options_()
        failUnless(result['test_bool'].value is True)
        failUnlessEqual(2, result['test_int'].value)
        failUnlessEqual('one', result['test_choice'].value)


if __name__ == '__main__':
    runModule()
