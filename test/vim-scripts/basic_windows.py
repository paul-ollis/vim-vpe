import contextlib


with test_context('data-out/basic_windows.txt'):

    print('- Test-ID: windows-attr-types -')
    assert_equal('Windows', 'wins.__class__.__name__')
    assert_equal(len(_vim.windows), 'len(vim.windows)')
    assert_true('isinstance(wins, vpe.windows.Windows)')

    win = wins[0]
    assert_equal('Window', 'win.__class__.__name__')
    assert_true('isinstance(win, vpe.windows.Window)')

    for i, b in enumerate(vim.windows):
        assert_equal('Window', 'b.__class__.__name__', info=i)
    assert_equal(len(_vim.windows), 'i + 1')
