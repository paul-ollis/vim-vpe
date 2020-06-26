" Vim test support initialisation script.

py3 <<EOF
import sys

sys.modules.pop('vpe', None)

sys.modules.pop('buffers', None)
sys.modules.pop('commands', None)
sys.modules.pop('current', None)
sys.modules.pop('dictionaries', None)
sys.modules.pop('options', None)
sys.modules.pop('proxies', None)
sys.modules.pop('tabpages', None)
sys.modules.pop('variables', None)
sys.modules.pop('windows', None)

sys.modules.pop('vpe.buffers', None)
sys.modules.pop('vpe.commands', None)
sys.modules.pop('vpe.current', None)
sys.modules.pop('vpe.dictionaries', None)
sys.modules.pop('vpe.options', None)
sys.modules.pop('vpe.proxies', None)
sys.modules.pop('vpe.tabpages', None)
sys.modules.pop('vpe.variables', None)
sys.modules.pop('vpe.windows', None)

EOF

source ~/.vim3/vimrc.vim
source ~/.vim3/gvimrc.vim

messages clear
py3file vim-scripts/helpers.py
