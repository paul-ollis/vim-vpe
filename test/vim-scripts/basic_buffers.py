import contextlib


with test_context('data-out/basic_buffers.txt'):

    print('- Test-ID: buffers-attr-types -')
    assert_equal('Buffers', 'bufs.__class__.__name__')
    assert_equal(len(_vim.buffers), 'len(vim.buffers)')

    buf = bufs[1]
    assert_equal('Buffer', 'buf.__class__.__name__')
    assert_true('isinstance(buf, vpe.buffers.Buffer)')

    for i, b in enumerate(vim.buffers):
        assert_true('isinstance(b, vpe.buffers.Buffer)', info=i)
    assert_equal(len(_vim.buffers), 'i + 1')
