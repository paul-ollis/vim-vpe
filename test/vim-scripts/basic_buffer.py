import contextlib

# Get the first buffer.
for buf in vim.buffers:
    break

with test_context('data-out/basic_buffer.txt'):

    print('- Test-ID: buffer-attr-types -')
    assert_equal('Buffer', 'buf.__class__.__name__')
    assert_equal('Variables', 'buf.vars.__class__.__name__')
    assert_equal('Options', 'buf.options.__class__.__name__')

    for i, buf in enumerate(vim.buffers):
        assert_equal(_vim.buffers[buf.number].name, 'buf.name', info=i)
        assert_equal(_vim.buffers[buf.number].number, 'buf.number', info=i)
        assert_equal(_vim.buffers[buf.number].valid, 'buf.valid', info=i)

        assert_true('isinstance(buf.number, int)', info=i)
        assert_true('isinstance(buf.name, str)', info=i)
        assert_true('isinstance(buf.valid, bool)', info=i)

    print('- Test-ID: buffer-append -')
    buf, _buf = get_test_buffer()
    assert_true('_buf.name.endswith("/--TEST--")')

    # By default, mimic Vim's behaviour of an empty buffer actually containting
    # a single empty line.
    assert_equal(1, 'len(buf)')
    assert_equal('', 'buf[0]')
    buf.append('Line 1')
    assert_equal(2, 'len(_buf)')
    assert_equal('Line 1', '_buf[-1]')

    # When emptied using the 'clear' method, a Buffer generally acts as if it
    # has zero length.
    buf.clear()
    assert_equal(0, 'len(buf)', info='Cleared buf has 0 len')
    i = None
    for i, line in enumerate(buf):
        pass
    assert_true('i is None')
    buf.append('Line 1')
    assert_equal(1, 'len(buf)')
    assert_equal(1, 'len(_buf)')
    assert_equal('Line 1', '_buf[-1]')

    # The *nr* argument can be used to insert a line.
    # Note that, the vpe.Buffer allows nr to be used as a keyword argument.
    buf.append('Line 3')
    buf.append('Line 2', nr=1)
    assert_equal('Line 2', '_buf[1]')
    buf.append('Line x', nr=0)
    assert_equal('Line x', '_buf[0]')

    # A list of lines can be appended
    buf[:] = []
    buf.append(['Line 2', 'Line 3'])
    assert_equal('', '_buf[0]')
    assert_equal('Line 2', '_buf[1]')
    assert_equal('Line 3', '_buf[2]')
    buf.append(['Line 4', 'Line 5'])
    assert_equal('Line 4', '_buf[3]')
    assert_equal('Line 5', '_buf[4]')

    # When emptied using the 'clear' method, appending a list does not leave
    # an empty first line.
    buf.clear()
    buf.append(['Line 1', 'Line 2'])
    assert_equal('Line 1', '_buf[0]')
    assert_equal('Line 2', '_buf[1]')
    assert_equal(2, 'len(buf)')
    assert_equal(2, 'len(_buf)')

    # The *nr* argument can be used to insert a list of lines.
    buf.append(['Line 1a', 'Line 2a'], nr=1)
    assert_equal('Line 1', '_buf[0]')
    assert_equal('Line 1a', '_buf[1]')
    assert_equal('Line 2a', '_buf[2]')

    # Various slices work correctly.
    buf.clear()
    assert_equal([], 'buf[:]')
    buf.append('')
    buf[:] = []
    assert_equal([''], 'buf[:]')

    buf[:] = [f'{i}' for i in range(5)]
    assert_equal(['1', '2'], 'buf[1:3]')
    assert_equal(['0', '2', '4'], 'buf[::2]')

    print('- Test-ID: buffer-marks -')
    _vim.command(f'buffer {_buf.number}')
    buf[:] = [f'Line {i + 1}' for i in range(5)]
    w = _vim.current.window
    w.cursor = 2, 3
    _vim.command('normal ma')
    w.cursor = 4, 5
    assert_equal((2, 3), "buf.mark('a')")
