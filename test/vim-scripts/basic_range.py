import contextlib

buf, _buf = get_test_buffer()
_buf[:] = [f'{i}' for i in range(10)]
del _buf[0]
rng = buf.range(3, 8)
_rng = rng._proxied

with test_context('data-out/basic_range.txt'):

    print('- Test-ID: range-attr-types -')
    assert_equal('Range', 'rng.__class__.__name__')

    print('- Test-ID: range-append -')

    # An emptied range has zero length.
    rng[:] = []
    assert_equal(0, 'len(rng)', info='Cleared rng has 0 len')
    i = None
    print(iter(rng))
    for i, line in enumerate(rng):
        pass
    assert_true('i is None')
    rng.append('Line 1')
    assert_equal(1, 'len(rng)')
    assert_equal(1, 'len(_rng)')
    assert_equal('Line 1', '_rng[-1]')

    # The *nr* argument can be used to insert a line.
    # Note that, the vpe.Range allows nr to be used as a keyword argument.
    rng.append('Line 3')
    rng.append('Line 2', nr=1)
    assert_equal('Line 2', '_rng[1]')
    rng.append('Line x', nr=0)
    assert_equal('Line x', '_rng[0]')

    # A list of lines can be appended
    rng[:] = []
    rng.append(['Line 1', 'Line 2'])
    assert_equal('Line 1', '_rng[0]')
    assert_equal('Line 2', '_rng[1]')
    rng.append(['Line 3', 'Line 4'])
    assert_equal('Line 3', '_rng[2]')
    assert_equal('Line 4', '_rng[3]')
    assert_equal(4, 'len(rng)')
    assert_equal(4, 'len(_rng)')

    # The *nr* argument can be used to insert a list of lines.
    rng.append(['Line 1a', 'Line 2a'], nr=1)
    assert_equal('Line 1', '_rng[0]')
    assert_equal('Line 1a', '_rng[1]')
    assert_equal('Line 2a', '_rng[2]')

    # Various slices work correctly.
    _rng[:] = []
    assert_equal([], 'rng[:]')
    _rng[:] = [f'{i}' for i in range(5)]
    assert_equal(['1', '2'], 'rng[1:3]')
    assert_equal(['0', '2', '4'], 'rng[::2]')

    for i, line in enumerate(rng):
        print(line)

    # import inspect
    # print(inspect.currentframe().f_lineno)

