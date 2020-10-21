#!/usr/bin/env python
"""Script to create the release tarball."""

from pathlib import Path
import os
import zipfile


def walk_relpaths(dirpath: Path):
    """Walk a directory tree, selecting release files."""
    for dirname, dirnames, filenames in os.walk(dirpath):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        dirnames[:] = [d for d in dirnames if not d.startswith('__')]
        for name in filenames:
            path = Path(dirname) / name
            if path.suffix in ('.swp', '.swn', '.swo', '.pyi'):
                continue
            yield path


def generate():
    """Generate the relase zip file."""
    root = Path(__file__).parent.parent.parent
    with zipfile.ZipFile(
            'vim-vpe.zip', mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        os.chdir('..')
        for sub_dir in ('docs/html', 'start', 'vpe'):
            subdir_path = root / 'vim-vpe'/ sub_dir
            for path in walk_relpaths(subdir_path):
                relpath = path.relative_to(root)
                zf.write(str(relpath))


generate()

# .
# ├── admin
# │   └── mk-release.py
# ├── dbuild
# ├── doc
# │   ├── html
# │   │   ├── api
# │   │   ├── vpe-help.html
# │   │   └── vpe.html
# │   │
# ├── README.rst
# ├── start
# │   └── vpe
# │       ├── doc
# │       │   ├── tags
# │       │   └── vpe-help.txt
# │       └── plugin
# │           └── vpe.vim
# └── vpe
#     ├── channels.py
#     ├── colors.py
#     ├── common.py
#     ├── core.py
#     ├── __init__.py
#     ├── mapping.py
#     ├── syntax.py
#     └── wrappers.py
