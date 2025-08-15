"""Wrapping of Vim types."""
# pylint: disable=deprecated-method

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support

import vpe

_run_after = ['test_vim.py']


class ListWrapping(support.Base):
    """VPE support for wrapped lists."""

    @test(testID='list-insert')
    def list_supports_insert(self):
        """A list supports the insert method.

        :<py>:

            vim_code = '''
            function! Make_list()
                return [1, 2, 4, 5]
            endfunction
            '''
            vim.command(vim_code)
            make_list = vpe.common.Function('Make_list')

            res = Struct()
            mylist = make_list()
            res.original = list(mylist)
            mylist.insert(2, 3)
            res.updated = list(mylist)

            dump(res)
        """
        res = self.run_self()
        failUnlessEqual([1, 2, 4, 5], res.original)
        failUnlessEqual([1, 2, 3, 4, 5], res.updated)


class DictWrapping(support.Base):
    """VPE support for wrapped dictionaries."""

    def suiteSetUp(self):
        """Called to set up the suite.

        :<py>:

            vim_code = '''
            function! Make_dict()
                return {'a': [1], 'b': [1, 2, 3]}
            endfunction
            '''
            vim.command(vim_code)
            make_dict = vpe.common.Function('Make_dict')
        """
        super().suiteSetUp()
        self.run_self()

    @test(testID='dict-iteration')
    def dict_iteration(self):
        """The Dictionary proxy supports expected iteration.

        A :vim:`python-Dictionary` does not iterate as expected. The Dictionary
        wrapper 'fixes' this.

        :<py>:

            res = Struct()
            v = make_dict()
            res.type = type(v)
            res.keys = sorted(list(v))
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['a', 'b'], res.keys)
        failUnless(res.type is vpe.common.MutableMappingProxy)

    @test(testID='dict-get-wraps')
    def dict_get(self):
        """The get method returns a wrapped item.

        A default may be provided or allowed to default to ``None``.

        :<py>:

            res = Struct()
            v = make_dict()
            res.b_list = v.get('b')
            res.def_num = v.get('unknown', 123)
            res.def_str = v.get('unknown', default='hi')
            res.def_none = str(v.get('unknown'))
            dump(res)
        """
        res = self.run_self()
        failUnless(isinstance(res.b_list, vpe.common.MutableSequenceProxy))
        failUnlessEqual('None', res.def_none)
        failUnlessEqual(123, res.def_num)
        failUnlessEqual('hi', res.def_str)

    @test(testID='dict-str-keys')
    def dict_str_keys(self):
        """The keys method returns a list of strings.

        The Vim Dictionary returns byte values, which is inconvenient.

        :<py>:

            res = Struct()
            v = make_dict()
            res.keys = v.keys()
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['a', 'b'], res.keys)

    @test(testID='dict-values')
    def dict_values(self):
        """The values method returns a list of wrapped/decoded items.

        :<py>:

            res = Struct()
            v = make_dict()
            res.values = [el.__class__.__name__ for el in v.values()]
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(
            ['MutableSequenceProxy', 'MutableSequenceProxy'], res.values)

    @test(testID='dict-items')
    def dict_items(self):
        """The items method returns a list of wrapped/decoded tuples.

        :<py>:

            res = Struct()
            v = make_dict()
            res.keys = [k for k, _ in v.items()]
            res.values = [el.__class__.__name__ for _, el in v.items()]
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['a', 'b'], res.keys)
        failUnlessEqual(
            ['MutableSequenceProxy', 'MutableSequenceProxy'], res.values)

    @test(testID='dict-pop-wraps')
    def dict_pop(self):
        """The pop method returns a wrapped item.

        A default may be provided, including ``None``. A KeyError can occur if
        no default is provided.

        :<py>:

            res = Struct()
            v = make_dict()
            res.b_list = v.pop('b')
            res.def_none = str(v.pop('unknown', default=None))
            res.def_num = v.pop('unknown', 123)
            dump(res)
        """
        res = self.run_self()
        failUnless(isinstance(res.b_list, vpe.common.MutableSequenceProxy))
        failUnlessEqual('None', res.def_none)
        failUnlessEqual(123, res.def_num)

    @test(testID='dict-popitem-wraps')
    def dict_popitem(self):
        """The pop method returns a wrapped item.

        :<py>:

            res = Struct()
            v = make_dict()
            res.item = v.popitem()
            dump(res)
        """
        res = self.run_self()
        failUnless(isinstance(res.item[0], str))
        failUnless(isinstance(res.item[1], vpe.common.MutableSequenceProxy))

    @test(testID='dict-del')
    def dict_del(self):
        """Wrapped dictionary items can be popped.

        :<py>:

            res = Struct()
            v = make_dict()
            del v['b']
            res.keys = v.keys()
            dump(res)
        """
        res = self.run_self()
        failUnlessEqual(['a'], res.keys)

    @test(testID='dict-membership')
    def dict_membership(self):
        """The membership tests work.

        Note that string and byte values work as keys.

        :<py>:

            res = Struct()
            v = make_dict()
            res.is_in_a = 'a' in v
            res.is_in_ab = b'a' in v
            res.has_a = v.has_key('a')
            res.has_ab = v.has_key(b'a')
            dump(res)
        """
        res = self.run_self()
        failUnless(res.is_in_a)
        failUnless(res.is_in_ab)
        failUnless(res.has_a)
        failUnless(res.has_ab)


if __name__ == '__main__':
    runModule()
