"""Special support for options."""

import vim as _vim

import vpe
from vpe import proxies
from vpe import variables

_comma_options = set((
    "belloff", "bo",
    "cdpath", "cd",
    "completepopup", "cpp",
    "isfname", "isf",
    "isident", "isi",
    "iskeyword", "isk",
    "isprint", "isp",
    "path", "pa",
    "previewpopup", "pvp",
    "varsofttabstop", "vsts",
    "vartabstop", "vts",
))

_single_comma_options = set((
    "backspace", "bs",
    "backupcopy", "bkc",
    "backupdir", "bdir",
    "backupskip", "bsk",
    "breakindentopt", "briopt",
    "casemap", "cmp",
    "cinkeys", "cink",
    "cinoptions", "cino",
    "cinwords", "cinw",
    "clipboard", "cb",
    "colorcolumn", "cc",
    "comments", "com",
    "complete", "cpt",
    "completeopt", "cot",
    "cscopequickfix", "csqf",
    "cursorlineopt", "culopt",
    "dictionary", "dict",
    "diffopt", "dip",
    "directory", "dir",
    "display", "dy",
    "errorformat", "efm",
    "eventignore", "ei",
    "fileencodings", "fencs",
    "fileformats", "ffs",
    "fillchars", "fcs",
    "foldclose", "fcl",
    "foldmarker", "fmr",
    "foldopen", "fdo",
    "grepformat", "gfm",
    "guicursor", "gcr",
    "guifont", "gfn",
    "guifontset", "gfs",
    "guifontwide", "gfw",
    "helplang", "hlg",
    "highlight", "hl",
    "indentkeys", "indk",
    "keymodel", "km",
    "langmap", "lmap",
    "lispwords", "lw",
    "listchars", "lcs",
    "matchpairs", "mps",
    "mouseshape", "mouses",
    "nrformats", "nf",
    "packpath", "pp",
    "printoptions", "popt",
    "renderoptions", "rop",
    "runtimepath", "rtp",
    "scrollopt", "sbo",
    "selectmode", "slm",
    "sessionoptions", "ssop",
    "spellfile", "spf",
    "spelllang", "spl",
    "spellsuggest", "sps",
    "suffixes", "su",
    "suffixesadd", "sua",
    "switchbuf", "swb",
    "tags", "tag",
    "thesaurus", "tsr",
    "toolbar", "tb",
    "undodir", "udir",
    "viewoptions", "vop",
    "viminfo", "vi",
    "viminfofile", "vif",
    "virtualedit", "ve",
    "whichwrap", "ww",
    "wildignore", "wig",
    "wildmode", "wim",
    "wildoptions", "wop",
))

_flag_options = set((
    "breakat", "brk",
    "cpoptions", "cpo",
    "formatoptions", "fo",
    "guioptions", "go",
    "mouse",
    "shortmess", "shm",
    "whichwrap", "ww",
))


class ListOption(str):
    """Extended string used for optiona that represent a list of value.

    This supports the '+=' and '-=' operations.
    """
    def __new__(cls, value, flag_style):
        if isinstance(value, bytes):
            value = value.decode()
        inst = super().__new__(cls, value)
        inst._flag_style = flag_style
        return inst

    def __iadd__(self, value):
        if not isinstance(value, str):
            raise TypeError(
                f'List style options only support strings.')
        parts = self._split(self)
        for v in self._split(value):
            if not self._flag_style or v not in parts:
                parts.append(v)
        return self._sep.join(parts)

    def __isub__(self, value):
        if not isinstance(value, str):
            raise TypeError(
                f'List style options only support strings.')
        parts = self._split(self)
        for v in self._split(value):
            if v in parts:
                parts.remove(v)
        return self._sep.join(parts)


class CommaListOption(ListOption):
    """Extended string used for single comma style options.

    This supports the '+=' and '-=' operations.
    """
    _sep = ','

    def _split(self, s):
        if s == '':
            return []
        return s.split(',')


class CharListOption(ListOption):
    """Extended string used for character list options.

    This supports the '+=' and '-=' operations.
    """
    _sep = ''

    def _split(self, s):
        return list(s)


class Options(variables.ImmutableVariables):
    """Wrapper for buffer.options, *etc.*

    This extends the behaviour so that options appear as attributes. The
    standard dictionary style access still works.
    """
    def __init__(self, options):
        self.__dict__['_proxied'] = options

    def __setattr__(self, name, value):
        if name not in self._proxied:
            raise AttributeError(
                f'{self.__class__.__name__} object has no attribute {name!r}')
        self._proxied[name] = self._resolve_item(value)

    def _wrap_item(self, value, name=None):
        if name in _comma_options or name in _single_comma_options:
            return CommaListOption(value, flag_style=name in _flag_options)
        elif name in _flag_options:
            return CharListOption(value, flag_style=True)
        elif isinstance(value, bytes):
            return value.decode()
        else:
            return super()._wrap_item(value)


class GlobalOptions(Options):
    """Wrapper for vim.options, *etc.*

    This extends the behaviour so that options appear as attributes. The
    standard dictionary style access still works.
    """
    def __getattr__(self, name):
        v = super().__getattr__(name)
        if v is None:
            oname_form = f'+{name}'
            if vpe.vim_eval(f'exists({oname_form!r})') == '0':
                oname = self.__class__.__name__
                raise AttributeError(
                    f'{oname} object has no attribute {name!r}')
        return self._wrap_item(vpe.vim_eval(f'&g:{name}'), name)

    def __setattr__(self, name, value):
        try:
            super().__setattr__(name, value)
            # raise AttributeError
            return
        except AttributeError as e:
            oname_form = f'+{name}'
            if vpe.vim_eval(f'exists({oname_form!r})') == '0':
                raise e
        v = int(value) if isinstance(value, bool) else value
        v_expr = repr(v)
        if v_expr[0] == "'":
            # Convert single quoted string expression to double quoted form.
            s = v_expr[1:-1]
            s = s.replace('"', r'\"')
            s = s.replace(r"\'", "'")
            v_expr = '"' + s + '"'
        vpe.vim_command(f'let &{name} = {v_expr}')


global_options = GlobalOptions(_vim.options)
