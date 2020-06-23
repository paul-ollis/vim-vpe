import contextlib

with test_context('data-out/basic_tabpage.txt'):

    print('- Test-ID: tabpage-attr-types -')
    assert_equal('TabPage', 'tab.__class__.__name__')
    assert_equal('Variables', 'tab.vars.__class__.__name__')

    for i, tab in enumerate(vim.tabpages):
        _tab = tab._proxied
        assert_equal(i + 1, 'tab.number')
        assert_equal(_vim.tabpages[i].number, 'tab.number', info=i)
        assert_equal(_vim.tabpages[i].valid, 'tab.valid', info=i)
        assert_equal(
            _vim.tabpages[i].window.number, 'tab.window.number', info=i)

        assert_true('isinstance(tab.number, int)', info=i)
        assert_true('isinstance(tab.valid, bool)', info=i)
