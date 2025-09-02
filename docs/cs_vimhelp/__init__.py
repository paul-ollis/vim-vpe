"""Sphinx extensions to work with Vim help files.

This provides:

- A Sphinx builder to generate Vim help files.
- A transformer to convert vim help references to vimhelp.org URLs.
"""

import functools
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
from typing import Any

from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx import roles
from sphinx.transforms import SphinxTransform

from . import vim_builder

tagmap = {}

vimhelp_org = 'https://vimhelp.org'


def get_date(*_args):
    return time.strftime('%b %Y', time.gmtime(time.time()))


def setup(app):
    app.add_builder(vim_builder.VimBuilder)
    app.add_config_value("vim_version", "8.0", "env")
    app.add_config_value("vim_date", get_date, "env")
    app.add_config_value("vim_link_map", {}, "env")
    app.add_transform(VimRefTransform)
    app.add_generic_role(
        'vim', functools.partial(nodes.inline, classes=['vim']))

    load_vim_tags()

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }


def lookup_helpfile(text):
    if text in tagmap:
        return tagmap[text]
    partials = [key for key in tagmap if key.startswith(text)]
    if len(partials) == 1:
        return tagmap[partials[0]]


class VimRefWalker(visitor.Visitor):
    def enter_inline(self, node, level):
        classes = node.attributes.get('classes', [])
        if 'vim' not in classes:
            return
        text = node.astext()
        helpfile = lookup_helpfile(text)
        if helpfile is None:
            return

        for n in node.attributes:
            node.attributes[n] = ''
        url_text = urllib.parse.quote(text)
        ref = nodes.reference(
            text=text, name=text,
            refuri=f'{vimhelp_org}/{helpfile}.html#{url_text}')
        node.replace_self(ref)


class VimRefTransform(SphinxTransform):
    """Convert :vim:`...` references to vimhelp.org URLs."""
    default_priority = 700

    def apply(self, **kwargs: Any) -> None:
        if self.app.builder.name != 'vimhelp':
            walker = VimRefWalker(self.document)
            self.document.walkabout(walker)


class Options:
    def __getattr__(self, name):
        return None


class Null:
    def write(self, *args):
        pass

    isatty = flush = writelines = close = write


options = Options
log = Null()
err = sys.stderr


def setOptions(theOptions):
    global options
    options = theOptions


def setLogPath(path):
    global log

    if path is None:
        if isinstance(log, Null):
            log.close()
        log = Null()
    else:
        if isinstance(log, Null):
            log = open(path, "w")


def load_vim_tags():
    """Scan Vim's help tags to build a mapping from name to help file.

    This is used to convert things RST text like :vim:`echo` to a vimhelp.org
    URL.
    """
    with tempfile.NamedTemporaryFile(mode='wt', delete=False) as f:
        out_path = f.name
    with tempfile.NamedTemporaryFile(mode='w+t', delete=False) as f:
        put = functools.partial(print, file=f)
        put(f':redir! >{out_path}')
        put(':echomsg globpath(&rtp, "**/doc/tags")')
        put(':redir END')
        put(':quit!')
        script_path = f.name

    # Run the above script to get a list fo Vim help tagfiles in a temporary
    # file.
    subprocess.run(
        ['vim', '-u', 'NONE', '-s', script_path], stderr=subprocess.DEVNULL)
    os.unlink(script_path)

    # Read the tag file names from the temporary file.
    with open(out_path,mode='rt') as f:
        lines = [line.strip() for line in f.read().split('^@')]
    os.unlink(out_path)

    # Process the tag files to build a map from tag name to help file name.
    for path in lines:
        if '/share/' in path:
            with open(path, 'rt') as f:
                for line in f:
                    name, helpfile, *_ = line.split()
                    tagmap[name] = helpfile
