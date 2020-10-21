# -*- coding: utf-8 -*-
"""Sphinx builder to create Vim help files.

"""
__docformat__ = "restructuredtext"

from typing import Any, Dict, Iterable, List, Tuple, Union
import pathlib

from docutils.io import StringOutput

from sphinx.builders import Builder
from sphinx.util.osutil import ensuredir
from sphinx.util.console import bold, darkgreen
from sphinx.util.nodes import inline_all_toctrees
from sphinx.util import logging

from .vim_writer import VimWriter

log = logging.getLogger(__name__)


class VimBuilder(Builder):
    name = 'vimhelp'
    format = 'vimhelp'
    out_suffix = '.txt'

    def init(self):
        pass

    def get_outdated_docs(self):
        return "all documents"

    def get_target_uri(self, docname, typ=None):
        if typ == 'token':
            return ''
        return docname

    def prepare_writing(self, docnames):
        self.writer = VimWriter(self)

    def assemble_doctree(self):
        master = self.config.master_doc
        tree = self.env.get_doctree(master)
        tree = inline_all_toctrees(
            builder=self,
            docnameset=set(),
            docname=master,
            tree=tree,
            colorfunc=darkgreen,
            traversed=[])
        tree['docname'] = master
        self.env.resolve_references(tree, master, self)
        #self.fix_refuris(tree)
        return tree

    def write_doc(self, docname, doctree):
        if docname != self.config.master_doc:
            return
        dest = pathlib.Path(self.outdir) / f'{docname}.txt'
        doctree = self.assemble_doctree()

        destination = StringOutput(encoding='utf-8')
        self.writer.write(doctree, destination)
        f = open(dest, "w")
        f.write(self.writer.output)
        f.close()

    def finish(self):
        pass
