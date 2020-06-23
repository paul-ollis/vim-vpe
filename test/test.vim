py3 <<EOF
import sys

sys.modules.pop('vpe', None)
sys.modules.pop('vpe.buffers', None)
sys.modules.pop('vpe.commands', None)
sys.modules.pop('vpe.options', None)
sys.modules.pop('vpe.proxies', None)
sys.modules.pop('vpe.dictionaries', None)
sys.modules.pop('vpe.variables', None)
sys.modules.pop('buffers', None)
sys.modules.pop('commands', None)
sys.modules.pop('options', None)
sys.modules.pop('proxies', None)
sys.modules.pop('dictionaries', None)
sys.modules.pop('variables', None)
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
