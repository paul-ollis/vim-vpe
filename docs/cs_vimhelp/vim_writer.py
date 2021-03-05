# -*- coding: utf-8 -*-
"""Writer that generates Vim help format output."""

from typing import Iterable, List
import collections
import contextlib
import io
import itertools
import os
import queue
import string
import sys
import textwrap
import threading
import weakref

from docutils import nodes
from docutils import writers

import cs_vimhelp
from . import table
from . import visitor

_source_path = None
_uc_open_quote = chr(8216)
_uc_close_quote = chr(8217)


class PushBackIterator:
    """An iterator that supports pushing items back.

    This was written to support simple text parsing, in which you need some
    amount of look-ahead and back-tracking. Whilst back-tracking may be
    considered harmful in parsers, for many simple tasks it is actually
    a perfectly adequate approach.
    """
    def __init__(self, it):
        """Constructor:

        :Param it:
            An iterable object.
        """
        self._it = iter(it)
        self._ungotten = []

    def __next__(self):
        """Iterator protocol: get next element

        If any items have been pushed back, then the most recently pushed item
        is returned. Otherwise we try to get the next new item.
        """
        if self._ungotten:
            return self._ungotten.pop()
        return next(self._it)
    next = __next__

    def peek(self):
        """Peek the next element

        If any items have been pushed back, then the most recently pushed item
        is returned. Otherwise we try to get the next new item.

        """
        if not self._ungotten:
            try:
                self.pushBack(next(self._it))
            except StopIteration:
                return
        return self._ungotten[-1]

    def pushBack(self, v):
        """Push `v` back into the iterator.

        :Param v:
            This can be anything, although it would normally be an item
            previously returned by `next`.
        """
        self._ungotten.append(v)

    #: An alias for pushBack
    unget = pushBack

    def __iter__(self):
        """A PushBackIterator is its own iterator."""
        return self


def handler():
    node = 0
    while node is not None:
        node = (yield None)


class RNode:
    """A node contianing information on how to render help text."""
    def __init__(self, parent, node):
        if parent is not None:
            self._parent = weakref.ref(parent)
        else:
            self._parent = None
        self.node = node
        self.children = []

    @property
    def parent(self):
        return self._parent() if self._parent is not None else None

    def add_child(self, node):
        rnode = RNode(self, node)
        self.children.append(rnode)
        return rnode

    def walk(self, level=0):
        for child in self.children:
            yield level, child
            yield from child.walk(level=level + 1)


class Indent:
    """Context manager to indent sys.stdout.

    While active, output to sys.sdtout is indented by 4 spaces. Indent contexts
    nest, each adding an additional 4 spaces.

    This is implemented by buffering sys.stdout. Indentation is added when the
    context exits and the output is flushed.
    """
    ind = 0
    stack = []

    def __init__(self, n=4, bulleted=False, enumerated=False, enum_width=3):
        self.indent = n
        self.bulleted = bulleted
        self.enumerated = itertools.count(1) if enumerated else None
        self.enum_width = enum_width

    def __enter__(self):
        self.f = io.StringIO()
        self.saved, sys.stdout = sys.stdout, self.f
        self.__class__.ind += self.indent
        self.stack.append(weakref.proxy(self))

    def __exit__(self, exc_type, exc_value, exc_tb):
        sys.stdout = self.saved
        text = self.f.getvalue()
        hang = self.prefix()
        prefix1 = ' ' * self.indent + hang
        prefix = ' ' * (self.indent + len(hang))
        blanks_done = False
        for line in self.f.getvalue().splitlines():
            if line.strip():
                if not blanks_done:
                    put(f'{prefix1}{line.rstrip()}')
                else:
                    put(f'{prefix}{line.rstrip()}')
                blanks_done = True
            else:
                put('')
        self.__class__.ind -= self.indent
        self.stack.pop()

    def prefix(self) -> str:
        """Get the first line prefix for this block."""
        if len(self.stack) < 2:
            return ''
        return self.stack[-2].next_prefix()

    def next_prefix(self) -> str:
        """Get the next prefix for a child block."""
        if self.bulleted:
            return '- '
        if self.enumerated:
            n = f'{next(self.enumerated)}.'
            return f'{n:<{self.enum_width}} '
        return ''


def paragraphs(lines: List[str]) -> List[List[str]]:
    """Break a set of lines up into paragraphs."""
    para = []
    for line in lines:
        if line.strip():
            if para:
                if not line.strip(para[-1]):
                    yield para
                para = []
        para.append(line)
    if para:
        yield para


class Simplifier(visitor.Visitor):
    def __init__(self, document, full_ref_to_ref_text):
        super().__init__(document)
        self.full_ref_to_ref_text = full_ref_to_ref_text

    def unknown_departure(self, node):
        children = node.children
        if all(isinstance(c, nodes.Text) for c in children):
            new_node = nodes.Text(''.join(c.astext() for c in children))
            children[:] = [new_node]
            node.setup_child(new_node)
        super().unknown_departure(node)

    def collapse_text(self, node, level):
        classes = node.attributes.get('classes', [])
        for n in node.attributes:
            node.attributes[n] = ''
        text = node.astext()
        if 'vim' in classes:
            if text.startswith(':'):
                text = f'`{text}`'
            elif (text.startswith(_uc_open_quote)
                    and text.endswith(_uc_close_quote)):
                text = f"'{text[1:-1]}'"
            elif not text.startswith("'"):
                text = f'|{text}|'
        node.replace_self(nodes.Text(text))

    def enter_reference(self, node, level):
        rt = node.attributes.get("reftitle", None)
        internal = node.attributes.get("internal", False)
        if rt is not None and internal:
            suffix = ''
            ref_text = node.astext()
            if ref_text.endswith('()'):
                suffix = '()'
            text = f'|{self.full_ref_to_ref_text.get(rt, rt)}|{suffix}'
        else:
            text = node.astext()
        node.replace_self(nodes.Text(text))

    enter_emphasis = collapse_text
    enter_strong = collapse_text
    enter_inline = collapse_text
    enter_literal = collapse_text


class Enumerator(nodes.NodeVisitor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.level = 0
        self.counts = collections.defaultdict(lambda: 0)

    def unknown_visit(self, node):
        attributes = getattr(node, 'attributes', None)
        if attributes:
            attributes['enum_index'] = self.counts[self.level]
        self.counts[self.level] += 1
        self.level += 1

    def unknown_departure(self, node):
        self.counts[self.level] = 0
        self.level -= 1


class IterWalker(visitor.Visitor):
    def __init__(self, document, *args, **kwargs):
        super().__init__(document, *args, **kwargs)
        self.q = queue.Queue()

    def unknown_visit(self, node):
        super().unknown_visit(node)
        self.q.put((self.level, node))

    def unknown_departure(self, node):
        super().unknown_departure(node)


class IterSequencer(threading.Thread):
    def __init__(self, document):
        super().__init__()
        self.document = document
        self.walker = IterWalker(document)

    def run(self):
        self.document.walkabout(self.walker)
        self.walker.q.put(None)

    def nodes(self):
        self.start()
        while True:
            node = self.walker.q.get()
            if node is None:
                break
            yield node
        self.join()


class IterSequencer:
    def __init__(self, document):
        super().__init__()
        self.document = document
        self.walker = IterWalker(document)

    def run(self):
        self.document.walkabout(self.walker)
        self.walker.q.put(None)

    def nodes(self):
        self.run()
        while True:
            node = self.walker.q.get()
            if node is None:
                break
            yield node


class FlexIter:
    def __init__(self, iter):
        self.iter = iter
        self.ungotten = []
        self.last_item = None

    def unget(self, item=None):
        if item is not None:
            self.ungotten.append(item)
        else:
            self.ungotten.append(self.last_item)

    def __iter__(self):
        return self

    def __next__(self):
        if self.ungotten:
            item = self.ungotten.pop()
        else:
            item = next(self.iter)
        self.last_item = item
        return item


def node_walker(node):
    return FlexIter(IterSequencer(node).nodes())


def clean_ref(ref):
    """Clean up a reference.

    This removes the doubling up of leading parts of a reference name.
    TODO: I do not understand why this is happening.
    """
    parts = ref.split('.')
    if len(parts) >= 2 and parts[0] == parts[1]:
        parts.pop(0)
    return '.'.join(parts)


class VimWriter(writers.Writer):
    supported = ('vim',)
    settings_spec = ('No options here.', '', ())
    settings_defaults = {}

    output = None

    def __init__(self, builder):
        writers.Writer.__init__(self)
        self.builder = builder
        self.skip_blankline = False
        self._used_refids = set()
        self._not_handled = set()

    def translate(self):
        flattenSphinxTree(self.document)
        referator = VimReferator(self.document)
        self.document.walkabout(referator)

        self.full_ref_to_ref_text = {}
        for full_ref, refs in referator.ref_map.items():
            refs = sorted(refs, key=lambda r: len(r))
            self.full_ref_to_ref_text[full_ref] = refs[-1]

        walker = Simplifier(self.document, self.full_ref_to_ref_text)
        self.document.walkabout(walker)
        walker = Enumerator(self.document)
        self.document.walkabout(walker)

        if 1:
            visitor = VimVisitor(self.document, referator.ref_map)
            self.document.walkabout(visitor)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            nodes = node_walker(self.document)
            self.put_header()
            self.put_top_section(nodes)
            nums = [0]
            for level, node in nodes:
                if node.tagname == 'section':
                    nums[-1] += 1
                    self.put_section(nodes, level, node, nums=nums)
            put()
            put('vim:tw=78:ts=8:noet:ft=help:norl:cole=0:')

        output = []
        for line in f.getvalue().splitlines():
            if line.lstrip()[:1] == '\b':
                output.append(line.lstrip()[1:])
            else:
                output.append(line)
        self.output = '\n'.join(output)

    def dispatch(self, nodes, this_level, node):
        name = node.tagname.lower().replace('#', '')
        handler = getattr(self, f'put_{name}', None)
        if handler:
            handler(nodes, this_level, node)
        elif name not in self._not_handled:
            self._not_handled.add(name)

    def put_header(self):
        filename = "vpe.txt"
        parts = [
            f'*{filename}*', ' ',
            f'For Vim version {self.builder.config.vim_version}', ' ',
            f'{self.builder.config.vim_date}']
        extra = 79 - len(''.join(parts))
        if extra > 0:
            a = extra // 2
            b = extra - a
        parts[1], parts[3] = ' ' * a, ' ' * b
        put(''.join(parts))

    def put_desc(self, nodes, this_level, node):
        put()
        for level, node in iter_level(nodes, this_level):
            if node.tagname == 'desc_signature':
                self.put_desc_sigature(nodes, level, node)
            if node.tagname == 'desc_content':
                self.put_desc_content(nodes, level, node)

    def format_refids(self, node, prefix=''):
        refids = []
        ref_map = self.builder.config.vim_link_map
        for refid in node.attributes.get('ids', []):
            refid = clean_ref(refid)
            if is_naff_refname(refid):
                continue
            ref = self.full_ref_to_ref_text.get(refid)
            ref = ref_map.get(ref, ref)
            if ref and ref not in refids:
                if ref not in self._used_refids:
                    self._used_refids.add(ref)
                    refids.append(f'{prefix}{ref}')
            refid = ref_map.get(refid, refid)
            if refid not in refids:
                if refid not in self._used_refids:
                    self._used_refids.add(refid)
                    refids.append(f'{prefix}{refid}')

        if refids:
            return ' '.join(f'*{refid}*' for refid in refids)
        return ''

    def rjust(self, text):
        put(text.rjust(79 - Indent.ind))

    def put_desc_sigature(self, nodes, this_level, node):
        self.put_ref_item(node.astext(), self.format_refids(node))
        skip_over(nodes, this_level)
        self.skip_blankline = True

    def put_desc_content(self, nodes, this_level, node):
        with Indent(2):
            for level, node in iter_level(nodes, this_level):
                self.dispatch(nodes, level, node)

    def put_block_quote(self, nodes, this_level, node):
        with Indent(2):
            self.skip_blankline = True
            for level, node in iter_level(nodes, this_level):
                self.dispatch(nodes, level, node)

    def put_literal_block(self, nodes, this_level, node):
        with Indent(2):
            put('>')
            lines = trimlines(node.astext().splitlines())
            for line in lines:
                put(line)
            put('\b<')
            skip_over(nodes, this_level)
        self.skip_blankline = True

    def put_table(self, nodes, this_level, node):
        # Future: Take note of specified column widths.
        rows, widths = gather_rows(nodes, this_level)
        widths = alloc_widths(widths, 79 - Indent.ind - 1)

        t = table.Table(width_spec=widths)
        t.left_pad = ''
        t.right_pad = ''
        t.vert_border = t.top_border = t.bottom_border = t.vertex = ' '

        for ri, row in enumerate(rows):
            for ci, entry in enumerate(row):
                cell = t.add_cell(ri, ci)
                cell.text = entry.astext()
        with Indent(1):
            for line in t.render().splitlines():
                put(line)

    def put_definition_list(self, nodes, this_level, node):
        put('')
        with Indent(2):
            for level, node in iter_level(nodes, this_level):
                self.dispatch(nodes, level, node)

    def put_definition_list_item(self, nodes, this_level, node):
        if node.attributes.get('enum_index', 0) > 0:
            put()
        for level, node in iter_level(nodes, this_level):
            self.dispatch(nodes, level, node)

    def put_term(self, nodes, this_level, node):
        put(node.astext())

    def put_definition(self, nodes, this_level, node):
        self.skip_blankline = True
        with Indent(2):
            for level, node in iter_level(nodes, this_level):
                self.dispatch(nodes, level, node)

    def put_enumerated_list(self, nodes, this_level, node):
        w = 2 if len(node.children) < 10 else 3
        with Indent(2, enumerated=True, enum_width=w):
            for level, node in iter_level(nodes, this_level):
                self.dispatch(nodes, level, node)

    def put_bullet_list(self, nodes, this_level, node):
        with Indent(2, bulleted=True):
            for level, node in iter_level(nodes, this_level):
                self.dispatch(nodes, level, node)

    def put_list_item(self, nodes, this_level, node):
        with Indent(0):
            for level, node in iter_level(nodes, this_level):
                self.dispatch(nodes, level, node)

    def put_paragraph(self, nodes, this_level, node):
        if not self.skip_blankline:
            put()
        self.skip_blankline = False
        width = 79 - Indent.ind
        text = node.astext().replace('\n', ' ')
        lines = textwrap.wrap(
            text, replace_whitespace=False, expand_tabs=False,
            width=width)
        for line in lines:
            put(line)
        skip_over(nodes, this_level)

    def put_ref_item(self, item, refs):
        """Put an item and any reference anchors.

        This will put both on the same line if they fit well. Otherwise the
        refs will be output first.

        :item: The item to put.
        :refs: The references.
        """
        if not refs:
            put(item)
        else:
            totlen = len(item) + len(refs)
            if totlen < 75 - Indent.ind:
                gap = 79 - Indent.ind - totlen
                put(f'{item}{"":<{gap}}{refs}')
            else:
                self.rjust(refs)
                put(item)

    def put_section(self, nodes, this_level, node, nums):
        nums = nums + [0]
        put()
        if len(nums) <= 2:
            put('=' * (79 - Indent.ind) + '~')
        elif len(nums) <= 3:
            put('-' * (79 - Indent.ind) + '~')
        else:
            put()

        refs = self.format_refids(node, prefix='vpe.')
        for level, node in iter_level(nodes, this_level):
            if node.tagname == 'section':
                nums[-1] += 1
                with Indent(2):
                    self.put_section(nodes, level, node, nums=nums)
            elif node.tagname == 'title':
                secnum = '.'.join(str(i) for i in nums[:-1])
                self.put_ref_item(f'{secnum}. {node.astext()}~', refs)
            elif node.tagname == 'hlist':
                skip_over(nodes, level)
            else:
                self.dispatch(nodes, level, node)

    def put_top_section(self, nodes):
        for level, node in nodes:
            if node.tagname == 'section':
                break

        for level, node in nodes:
            if node.tagname == 'section':
                return nodes.unget()
            elif node.tagname == 'title':
                put()
                put(node.astext().center(79), add_blank=True)
            elif node.tagname == 'paragraph':
                self.put_paragraph(nodes, level, node)
            elif node.tagname == 'table':
                self.put_table(nodes, level, node)


class Struct:
    pass


def as_single_line(node):
    lines = node.astext().splitlines()
    return " ".join(lines)


class Para(list):
    def __init__(self, *args, **kwargs):
        self.ind = kwargs.pop("ind", 0)
        self.wrap = kwargs.pop("wrap", True)
        self.label = kwargs.pop("label", None)
        self.ind = " " * (self.ind * 2)
        self.pendParaSep = kwargs.pop("pendParaSep", 2)
        super(Para, self).__init__(*args, **kwargs)


class VimReferator(visitor.Visitor):
    def __init__(self, document, *args, **kwargs):
        visitor.Visitor.__init__(self, document, *args, **kwargs)
        self.ref_map = {}

    def isValidRef(self, s):
        for c in s:
            if c in string.ascii_letters:
                continue
            if c in string.digits:
                continue
            if c in '_-':
                continue
            return False
        return True

    def enter_reference(self, node, level):
        self.skipLevel = self.level
        rt = node.attributes.get("reftitle", None)
        internal = node.attributes.get("internal", False)
        if rt is None or not internal:
            return
        ref_text = node.astext()
        if ref_text.endswith("()"):
            ref_text = ref_text[:-2]
        if not self.isValidRef(ref_text):
            return

        self.ref_map.setdefault(rt, set()).add(ref_text)


class VimVisitor(visitor.Visitor):
    def __init__(self, document, ref_map, *args, **kwargs):
        visitor.Visitor.__init__(self, document, *args, **kwargs)
        # cs_vimhelp.setLogPath('/tmp/wibble.log')


def flattenSphinxTree(node):
    """Flatten the doctree created by Sphinx.

    Sphinx uses the compound node to group everything in a toctree
    directive and naturally these compound nodes can nest. So you can have
    something like::

      --o-- para1
        |-- para2
        |-- compound
        |   o--para5
        |   |
        |   |--compound
        |   |  o--para8
        |   |
        |   |--para6
        |   `--para7
        |-- para3
        |-- para4

    This function will reorganise the Sphinx tree to be::

      --o-- para1
        |-- para2
        |-- para3
        |-- para4
        |-- para4
        |-- para6
        |-- para7
        `-- para8

    Which is much more convenient when generating output for a single file,
    such as for vim help or a Word docx file.

    """
    atEnd = []
    newList = []
    for n in node.children:
        flattenSphinxTree(n)
        if n.tagname == "compound":
            atEnd.extend(n.children)
        else:
            newList.append(n)
    node.children = newList + atEnd


class OutputQueue:
    """An output queue of rendering operations.

    """
    def __init__(self):
        self.components = {}
        self.components["header"] = []
        self.components["toc"] = []
        self.components["body"] = []
        self.components["footer"] = []
        self._dest = [self.components["body"]]
        self.para = Para()
        self.children = []

    @property
    def dest(self):
        return self._dest[-1]

    def pushDest(self, name):
        self._dest.append(self.components[name])

    def popDest(self):
        self._dest.pop()

    def addItem(self, typ, data, dest):
        if dest:
            dest = self.components[dest]
        else:
            dest = self.dest
        dest.append((typ, data))

    def addTarget(self, target, dest=None):
        self.addItem("target", target, dest)

    def addText(self, text, dest=None):
        self.para.append(("text", text))

    def addReference(self, ref, text=None, dest=None):
        self.para.append(("ref", (ref, text)))

    def addEnumStart(self, enum_type, enum_count):
        self.addItem("enumStart", (enum_type, enum_count), None)

    def addEnumEnd(self):
        self.addItem("enumEnd", None, None)

    def addNewItem(self):
        self.addItem("newItem", None, None)

    def addPara(self, dest=None, ind=0, pendParaSep=2, wrap=True, label=None):
        self.para = Para(ind=ind, pendParaSep=pendParaSep, wrap=wrap,
                            label=label)
        self.addItem("para", self.para, dest)

    def addLitBlock(self, dest=None):
        self.para = Para()
        self.addItem("litPara", self.para, dest)

    def addTitle(self, text, dest=None):
        self.addItem("title", text, dest)

    def addIndent(self):
        self.addItem("indent", None, None)

    def addDedent(self):
        self.addItem("dedent", None, None)

    def addRubric(self, text, dest=None):
        self.addItem("rubric", text, dest)

    def addHeading(self, text, level, label, dest=None):
        self.addItem("heading", (text, level, label), dest)

    def addToc(self, text, level, label, dest="toc"):
        self.addItem("toc", (text, level, label), dest)

    def addContents(self):
        self.addItem("toc", None, "body")

    def _fmtLabeled(self, text, label, delim):
        l = len(text) + len(label) + 2 * len(delim)
        space = " " * (80 - l)
        return "%s%s%s%s%s" % (text, space, delim, label, delim)

    def delHeading(self, level, dest=None):
        toDel = []
        for i, (typ, data) in enumerate(self.components["body"]):
            if typ != "heading":
                continue
            text, lev, label = data
            if lev == level:
                toDel.append(i)
        for i in reversed(toDel):
            del self.components["body"][i]

    def render(self, f):
        self._render(f, self.components["header"], pendParaSep=0)
        if self.components["body"]:
            self._render(f, self.components["body"])
        if self.components["footer"]:
            self._render(f, self.components["footer"])

    def _do_contents(self, f):
        if not self.components["toc"]:
            return

        f.write("Contents:\n")
        hnum = [0]
        for typ, (text, level, label) in self.components["toc"]:
            if level < 2:
                continue
            n = level - 1
            if n > 0:
                if n > len(hnum):
                    hnum.append(0)
                hnum = hnum[:n]
                hnum[n - 1] += 1
            ent = "  %s. %s" % (".".join(str(v) for v in hnum), text)
            f.write("%s\n" % self._fmtLabeled(ent, label, '|'))
        f.write("\n")

    def _buildPara(self, para):
        parts = []
        for typ, data in para:
            if typ == "text":
                parts.append(data)
            elif typ == "ref":
                ref, text = data
                if text:
                    parts.append("%s->|%s|" % (text, ref))
                else:
                    parts.append("|%s|" % ref)
        return parts

    def _render(self, f, seq, pendParaSep=2):
        seq = PushBackIterator(seq)
        hnum = [0]
        ind = ""
        extraInd = ""
        target = None
        enum = []
        enumCount = 0
        enumFormat = None
        prefix = ""
        clearCount = 0

        for i, (typ, data) in enumerate(seq):
            if typ == "indent":
                extraInd += "  "
            elif typ == "dedent":
                extraInd = extraInd[:-2]
            elif typ == "enumStart":
                enum.append((enumCount, enumFormat))
                enumFormat, enumCount = data
                enumCount = int(enumCount)
            elif typ == "enumEnd":
                enumCount, enumFormat = enum.pop()
                prefix = ""
            elif typ == "newItem":
                n = str(enumCount) + "."
                prefix = "%-3s " % n
                enumCount += 1

            nextType = None
            v = seq.peek()
            if v:
                nextType = v[0]
            if typ == "litPara":
                if pendParaSep:
                    if i == 0:
                        f.write("\n>\n")
                    else:
                        f.write(" >\n\n")
            else:
                if pendParaSep:
                    f.write("\n" * pendParaSep)
            pendParaSep = 0

            if typ == "target":
                pass

            elif typ == "para":
                pendParaSep = data.pendParaSep
                text = "".join(self._buildPara(data))
                if data.wrap:
                    text = text.replace("\n", " ")
                    lines = textwrap.wrap(text, replace_whitespace=False,
                        expand_tabs=False, width=79)
                else:
                    lines = text.splitlines()
                if data.label:
                    f.write("%s\n" % self._fmtLabeled("", data.label, '*'))
                for i, line in enumerate(lines):
                    ind = data.ind + extraInd + prefix
                    if i:
                        f.write("\n")
                    f.write("%s%s" % (ind, line))
                    if enumFormat:
                        prefix = "    "
                    else:
                        prefix = ""

            elif typ == "litPara":
                lines = self._buildPara(data)
                pendParaSep = 2
                for i, block in enumerate(lines):
                    for j, line in enumerate(block.splitlines()):
                        if j or i:
                            f.write("\n")
                        if line.strip():
                            f.write("%s  %s" % (ind, line))
                f.write("\n<")

            elif typ == "title":
                pendParaSep = 2
                f.write(data + " ~")

            elif typ == "rubric":
                pendParaSep = 2
                f.write(" %s ~" % data)

            elif typ == "line":
                f.write("  %s\n" % data)

            elif typ == "heading":
                pendParaSep = 2
                text, level, label = data
                n = level - 1
                if n > 0:
                    if n > len(hnum):
                        hnum.append(0)
                    hnum = hnum[:n]
                    hnum[n - 1] += 1
                hdr = "%s. %s" % (".".join(str(v) for v in hnum), text)
                if level == 2:
                    f.write("%s\n" % ("=" * 79))
                f.write("%s" % self._fmtLabeled(hdr, label, '*'))

            elif typ == "toc":
                self._do_contents(f)


def gather_rows(nodes, this_level):
    rows = []
    widths = []
    for level, node in nodes:
        if level <= this_level:
            nodes.unget()
            break
        elif node.tagname == 'row':
            row = []
            rows.append(row)
        elif node.tagname == 'entry':
            row.append(node)
            n = len(row)
            if n > len(widths):
                widths.append(0)
            widths[n - 1] = max(widths[n - 1], len(node.astext()))

    return rows, widths


def alloc_widths(widths, avail_width):
    widths = list(widths)
    n = len(widths)
    space = avail_width - (n + 1) * 2 - n
    per_col = space // len(widths)
    oversized = []
    undersized = []
    unallocated = space
    for i, w in enumerate(widths):
        if w > per_col:
            oversized.append(i)
        else:
            unallocated -= w
            undersized.append(w)
    if oversized:
        if undersized:
            per_col = max(unallocated // len(oversized), max(undersized))
        else:
            per_col = unallocated // len(oversized)
        for i in oversized:
            widths[i] = per_col
    return widths


def put(text='', add_blank=False):
    if text is None:
        return
    if isinstance(text, str):
        print(text)
    else:
        print('\n'.join(text))
    if add_blank:
        print()


def trimlines(lines: Iterable[str]) -> List[str]:
    """Remove leading and trainling blank lines from a sequence.

    :lines: A iterable containing the lines to be cleaned.
            [%consumed]
    :return: A new list of cleaned lines.
    """
    newlines = list(lines)
    while newlines and not newlines[0].strip():
        newlines.pop(0)
    while newlines and not newlines[-1].strip():
        newlines.pop()
    return newlines


def skip_to(nodes, name):
    for level, node in nodes:
        if node.tagname == name:
            return nodes.unget()


def iter_level(nodes, this_level):
    for level, node in nodes:
        if level <= this_level:
            return nodes.unget()
        yield level, node


def skip_over(nodes, this_level):
    for _ in iter_level(nodes, this_level):
        pass


def is_naff_refname(name):
    if name.endswith('-0'):
        return True
