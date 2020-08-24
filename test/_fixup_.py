"""Special environment fix-ups for the tests."""

import pathlib
import sys

sys.path.append(str(pathlib.Path.cwd().parent))
sys.path.append(str(pathlib.Path.cwd().parent / 'stub'))
