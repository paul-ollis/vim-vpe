py3 <<EOF
import sys

_vpe_modules = (
    'buffers', 'commands', 'current', 'dictionaries', 'options',
    'proxies', 'tabpages', 'variables', 'windows',
]
for name in _vpe_modules:
    sys.modules.pop(f'vpe.{name}', None)
    sys.modules.pop(f'{name}', None)
sys.modules.pop('vpe', None)
EOF

source ~/.vim3/vimrc.vim
source ~/.vim3/gvimrc.vim
let x = 3

py3 <<EOF
import vpe
vim = vpe.Vim()

print(len(vim.buffers))
for b in vim.buffers:
    print(f'{b.number=} {len(b)=} {b.name=}')
    for i, line in enumerate(b):
        print(f'  {i}: {line!r}')
        if i > 3:
            break

print(f'{list(vim.vars.keys())=}')

EOF
