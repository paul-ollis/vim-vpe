import contextlib


with test_context('data-out/basic_tabpages.txt'):

    print('- Test-ID: tabpages-attr-types -')
    assert_equal('TabPages', 'tabs.__class__.__name__')
    assert_equal(len(_vim.tabpages), 'len(vim.tabpages)')
    assert_true('isinstance(tabs, vpe.tabpages.TabPages)')

    tab = tabs[0]
    assert_equal('TabPage', 'tab.__class__.__name__')
    assert_true('isinstance(tab, vpe.tabpages.TabPage)')

    for i, b in enumerate(vim.tabpages):
        assert_equal('TabPage', 'b.__class__.__name__', info=i)
    assert_equal(len(_vim.tabpages), 'i + 1')
