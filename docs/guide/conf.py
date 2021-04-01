import os
import sys
sys.path.append(os.path.abspath(".."))
needs_sphinx = '3.2'
extensions = ['sphinx.ext.todo', 'cs_vimhelp', 'cs_vimhelp']
todo_include_todos = True
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'Vim Python Extensions'
copyright = 'paul@cleversheep.org'
version = 'dev'
release = 'dev'
exclude_patterns = []
pygments_style = 'manni'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
htmlhelp_basename = 'Vim Python Extensionsdoc'
html_theme_path = ['.']
html_theme_options = {}
default_role = 'any'
autodoc_typehints = 'none'
vim_link_map = {'vim': 'vpe.vim', 'Vim': 'vpe.Vim'}
