"""Extension module for Sphinx to create Vim help files.

"""

from sphinx import roles
from cs_sphinx_ext import vim_builder


def setup(app):
    app.add_builder(vim_builder.VimBuilder)
    app.add_config_value("vim_dest_path", "", "")
