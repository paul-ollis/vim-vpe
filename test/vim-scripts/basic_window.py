import contextlib

with test_context('data-out/basic_window.txt'):

    print('- Test-ID: window-attr-types -')
    assert_equal('Window', 'win.__class__.__name__')
    assert_equal('Variables', 'win.vars.__class__.__name__')
    assert_equal('Options', 'win.options.__class__.__name__')

    for i, win in enumerate(vim.windows):
        _win = win._proxied
        assert_equal(i + 1, 'win.number')
        assert_equal(_vim.windows[i].buffer.name, 'win.buffer.name', info=i)
        assert_equal(_vim.windows[i].number, 'win.number', info=i)
        assert_equal(_vim.windows[i].valid, 'win.valid', info=i)
        assert_equal(_vim.windows[i].height, 'win.height', info=i)
        assert_equal(_vim.windows[i].width, 'win.width', info=i)
        assert_equal(_vim.windows[i].row, 'win.row', info=i)
        assert_equal(_vim.windows[i].col, 'win.col', info=i)
        assert_equal(_vim.windows[i].cursor, 'win.cursor', info=i)
        assert_equal(
            _vim.windows[i].tabpage.number, 'win.tabpage.number', info=i)

        assert_true('isinstance(win.number, int)', info=i)
        assert_true('isinstance(win.valid, bool)', info=i)
        assert_true('isinstance(win.width, int)', info=i)
        assert_true('isinstance(win.height, int)', info=i)
        assert_true('isinstance(win.row, int)', info=i)
        assert_true('isinstance(win.row, int)', info=i)

    print('- Test-ID: window-writeable-attrs -')
    with double_split_window_context():
        win = vim.windows[0]
        w, h = win.width, win.height
        win.width = w + 1
        assert_equal(w + 1, 'win.width')
        win.height = h + 1
        assert_equal(h + 1, 'win.height')

    buf, _buf = get_test_buffer(goto=True)
    buf[:] = [f'Line {i + 1}' for i in range(5)]
    r, c = win.cursor
    print(r, c)
    win.cursor = r + 1, c + 1
    assert_equal((r + 1, c + 1), 'win.cursor')
