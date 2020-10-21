"""A visitor base class.

"""
__docformat__ = "restructuredtext"


import docutils.nodes

import vimhelp


class ProxyDict:
    def __init__(self, item):
        self.item = item

    def __getitem__(self, name):
        return self.item.get(name, None)


class Context:
    pass


class Visitor(docutils.nodes.NodeVisitor):
    """The base class for reStructuredText conversion.

    :Ivar level:
        The current level within the *docUtils* document tree that is being
        walked.
    :Ivar skipLevel:
        When non-zero, we do not skip nodes that are deeper in the tree.

    """
    def __init__(self, *args, **kwargs):
        docutils.nodes.NodeVisitor.__init__(self, *args, **kwargs)
        vimhelp.setLogPath(None)
        self.level = 0
        self.skipLevel = 0
        self._contextStack = []

    # My idea. Visit/departure maintain a stack. By default the stack stores
    # ``None``, but a significant node type, e.g. table, can poke a context
    # object. Other nodes can attach information to the most recent context.

    def unknown_visit(self, node):
        """Handler for all node visit processing.

        I let all nodes be effectively treated as unknown nodes. That way I can
        route all processing through `processNode`, which allos me to easily
        add tracing and simplify some other stuff as well.

        """
        self._contextStack.append(None)
        self.processNode("enter", node)

    def unknown_departure(self, node):
        """Handler for all node departure processing.

        See `unknown_visit` for why this is here.

        """
        self.processNode("leave", node)
        self._contextStack.pop()

    def addContext(self):
        assert self._contextStack[-1] is None
        self._contextStack[-1] = Context()

    def getContext(self):
        for c in reversed(self._contextStack):
            if c is not None:
                return c

    def processNode(self, mode, node):
        """Common processing for node visit and departure.

        This is invoked for *all* RST nodes. It looks for a method called
        ``enter_<name>`` or ``leave_<name>``, where ``<name>`` is the node's
        type (paragraph, Text, block_quote, etc). If a method can be found then
        it is normally invoked as ``method(node, self.level, ...)``. However,
        if self.skipLevel is currently non-zero then the method is not invoked.

        """
        if mode == "enter":
            self.level += 1
        else:
            if self.skipLevel and self.level <= self.skipLevel:
                self.skipLevel = 0
            self.level -= 1

        tracer = getattr(self, "log_%s" % mode)
        kwargs = {}
        name = node.__class__.__name__
        if len(name) == 2 and name.endswith("_"):
            kwargs["char"] = name[0]
            name = "Char"

        funcName = "%s_%s" % (mode, name)
        func = getattr(self, funcName, None)
        if func:
            if not self.skipLevel:
                try:
                    func(node, self.level, **kwargs)
                finally:
                    tracer(node, self.level, "  ")
            else:
                tracer(node, self.level, "..")
        else:
            tracer(node, self.level, "**")

    def log_enter(self, node, level, prefix=""):
        ignored = set(('enum_index',))
        sel_keys = ('ids',)
        text = ""
        name = node.__class__.__name__
        if name == "Text":
            text = " " + repr(node.astext()[:80])
        elif name in ("target", ):
            text = ": %s" % node.attributes.get("refid", "")
        elif name in ("index", 'definition_list_item', 'container'):
            text = 'x: ' + ' '.join(
                f'{n}={v!r}' for n, v in node.attributes.items()
                if n not in ignored and (str(v) == '0' or v))
        else:
            text = ' '.join(
                f'{n}={v!r}' for n, v in node.attributes.items()
                if n not in ignored and (str(v) == '0' or v))
            if 0:
                non_empty = [n for n, v in node.attributes.items() if v]
                text = ' '.join(
                    f'{n}={node.attributes[n]!r}' for n in sel_keys
                    if n in non_empty)
        vimhelp.log.write(
            f'{prefix}ENTER {level:<2}{" "*level} {node.__class__.__name__}'
            f' {text}\n')

    def log_leave(self, node, level, prefix=""):
        return
        vimhelp.log.write("%sLEAVE %s %s %s\n" % (prefix,
                level + 1, "  " * (level + 1),
                node.__class__.__name__))
