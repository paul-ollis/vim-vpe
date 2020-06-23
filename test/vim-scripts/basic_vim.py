import contextlib


def test_singletone(name):
    a = getattr(vim, name)
    b = getattr(vim, name)
    if id(a) == id(b):
        assert_true('True')
    else:
        assert_true('False', vim_attr=name, a=id(a), b=id(b))


with test_context('data-out/basic_vim.txt'):

    print('- Test-ID: vim-attr-types -')
    assert_equal('Vim', 'vim.__class__.__name__')
    assert_equal('module', 'vim.vim().__class__.__name__')
    assert_equal('Buffers', 'vim.buffers.__class__.__name__')
    assert_equal('Variables', 'vim.vars.__class__.__name__')
    assert_equal('Variables', 'vim.vvars.__class__.__name__')
    assert_equal('GlobalOptions', 'vim.options.__class__.__name__')
    assert_equal('Windows', 'vim.windows.__class__.__name__')
    assert_equal('TabPages', 'vim.tabpages.__class__.__name__')

    print('- Test-ID: vim-read-only-attrs -')
    assert_raises(AttributeError, 'setattr(vim, "buffers", _vim.buffers)')
    assert_raises(AttributeError, 'setattr(vim, "vars", _vim.vars)')
    assert_raises(AttributeError, 'setattr(vim, "vvars", _vim.vvars)')
    assert_raises(AttributeError, 'setattr(vim, "options", _vim.options)')
    assert_raises(AttributeError, 'setattr(vim, "windows", _vim.windows)')
    assert_raises(AttributeError, 'setattr(vim, "tabpages", _vim.tabpages)')
    assert_raises(AttributeError, 'setattr(vim, "current", _vim.current)')

    print('- Test-ID: vim-singletons -')
    test_singletone('buffers')
    test_singletone('vars')
    test_singletone('vvars')
    test_singletone('options')
    test_singletone('windows')
    test_singletone('tabpages')
    test_singletone('current')

    print('- Test-ID: comma-separated-flag-option -')
    options.whichwrap = ''
    assert_equal('', 'options.whichwrap')
    options['whichwrap'] = 'b,s,h'
    assert_equal('b,s,h', 'options.whichwrap')
    options.whichwrap -='s'
    assert_equal('b,h', 'options.whichwrap')
    options.whichwrap +='s'
    assert_equal('b,h,s', 'options.whichwrap')

    print('- Test-ID: flag-option -')
    options.mouse = 'na'
    assert_equal('na', 'options.mouse')
    options.mouse += 'nvic'
    assert_equal('navic', 'options.mouse')
    options.mouse -= 'ni'
    assert_equal('avc', 'options.mouse')

    print('- Test-ID: list-option -')
    saved = options.tags
    options.tags = ''
    assert_equal('', 'options.tags')
    options.tags += 'tags,random.tags'
    assert_equal('tags,random.tags', 'options.tags')
    options.tags += 'mytags,hertags'
    assert_equal('tags,random.tags,mytags,hertags', 'options.tags')
    options.tags -= 'tags,hertags'
    assert_equal('random.tags,mytags', 'options.tags')
    options.tags = saved

    print('- Test-ID: global-option -')
    options.cinwords = ''
    assert_equal('', 'options.cinwords')
    options.cinwords += 'for,if'
    assert_equal('for,if', 'options.cinwords')
    options.cinwords += 'else'
    assert_equal('for,if,else', 'options.cinwords')
    options.cinwords -= 'if'
    assert_equal('for,else', 'options.cinwords')
    assert_equal('for,else', 'vim.eval("&g:cinwords")')

    print('- Test-ID: mod-overrides-functions -')
    assert_true('isinstance(vim.bufnr, vpe.Function)')
    assert_false('isinstance(vim.eval, vpe.Function)')
