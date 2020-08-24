import vim as _vim
from . import buffers, proxies
from typing import Any, Optional, Union

class Scratch(buffers.Buffer):
    name: Any = ...
    def __init__(self, name: Any, buffer: Any) -> None: ...
    def show(self) -> None: ...
    def modifiable(self) -> proxies.TemporaryOptions: ...

class Log:
    fifo: Any = ...
    buf: Any = ...
    start_time: Any = ...
    text_buf: Any = ...
    saved_out: Any = ...
    def __init__(self, name: Any) -> None: ...
    def __call__(self, *args: Any) -> None: ...
    def redirect(self) -> None: ...
    def flush(self) -> None: ...
    def write(self, s: Any) -> None: ...
    def clear(self) -> None: ...
    def show(self) -> None: ...
    def set_maxlen(self, maxlen: int) -> None: ...

class Timer:
    def __init__(self, ms: Any, func: Any, repeat: Optional[Any] = ...) -> None: ...
    @property
    def id(self) -> int: ...
    @property
    def time(self) -> int: ...
    @property
    def repeat(self) -> int: ...
    @property
    def remaining(self) -> int: ...
    @property
    def paused(self) -> bool: ...
    def stop(self) -> None: ...
    def pause(self) -> None: ...
    def resume(self) -> None: ...
    @classmethod
    def stop_all(cls) -> None: ...

class _PopupOption:
    name: Any = ...
    def __init__(self, name: Any) -> None: ...

class _PopupROOption(_PopupOption):
    def __get__(self, obj: Any, _: Any): ...

class _PopupWOOption(_PopupOption):
    def __set__(self, obj: Any, value: Any) -> None: ...

class _PopupRWOption(_PopupROOption, _PopupWOOption): ...

class _PopupROPos(_PopupOption):
    def __get__(self, obj: Any, _: Any): ...

class _PopupWOPos(_PopupOption):
    def __set__(self, obj: Any, value: Any) -> None: ...

class _PopupRWPos(_PopupROPos, _PopupWOPos): ...

class Popup:
    def __init__(self, content: Any, **p_options: Any) -> None: ...
    @property
    def id(self) -> int: ...
    @property
    def buffer(self) -> buffers.Buffer: ...
    def hide(self) -> None: ...
    def show(self) -> None: ...
    def settext(self, content: Any) -> None: ...
    def close(self, result: int=...) -> None: ...
    @classmethod
    def clear(cls: Any, force: bool) -> None: ...
    def on_close(self, result: int) -> None: ...
    def on_key(self, key: str, byte_seq: bytes) -> bool: ...
    borderchars: Any = ...
    borderhighlight: Any = ...
    border: Any = ...
    col: Any = ...
    core_col: Any = ...
    core_line: Any = ...
    core_width: Any = ...
    cursorline: Any = ...
    drag: Any = ...
    firstline: Any = ...
    fixed: Any = ...
    flip: Any = ...
    height: Any = ...
    highlight: Any = ...
    lastline: Any = ...
    line: Any = ...
    mapping: Any = ...
    mask: Any = ...
    maxheight: Any = ...
    maxwidth: Any = ...
    minheight: Any = ...
    minwidth: Any = ...
    mousemoved: Any = ...
    moved: Any = ...
    padding: Any = ...
    pos: Any = ...
    resize: Any = ...
    scrollbar: Any = ...
    scrollbarhighlight: Any = ...
    tabpage: Any = ...
    textprop: Any = ...
    textpropid: Any = ...
    textpropwin: Any = ...
    thumbhighlight: Any = ...
    time: Any = ...
    title: Any = ...
    visible: Any = ...
    width: Any = ...
    wrap: Any = ...
    zindex: Any = ...
    close_control: Any = ...

class PopupAtCursor(Popup): ...
class PopupBeval(Popup): ...
class PopupNotification(Popup): ...

class PopupDialog(Popup):
    def on_key(self, key: Any, byte_seq: Any): ...

class PopupMenu(Popup):
    def on_key(self, key: Any, byte_seq: Any): ...

class Function(_vim.Function):
    def __call__(self, *args: Any, **kwargs: Any): ...

class Registers:
    def __getitem__(self, reg_name: Any): ...
    def __setitem__(self, reg_name: Any, value: Any): ...

class Vim:
    def __new__(cls, *args: Any, **kwargs: Any): ...
    def temp_options(self, **presets: Any): ...
    @property
    def registers(self) -> Registers: ...
    @staticmethod
    def vim(): ...
    @property
    def error(self) -> _vim.error: ...
    def __getattr__(self, name: Any): ...
    def __setattr__(self, name: Any, value: Any) -> None: ...

class Callback:
    callbacks: dict = ...
    caller: str = ...
    method: Any = ...
    ref_inst: Any = ...
    vim_args: Any = ...
    py_args: Any = ...
    py_kwargs: Any = ...
    pass_bytes: Any = ...
    info: Any = ...
    def __init__(self, func: Any, *, py_args: Any = ..., py_kwargs: Any = ..., vim_args: Any = ..., pass_bytes: bool = ..., info: Any = ...) -> None: ...
    def __call__(self, vim_args: Any, callargs: Any = ...): ...
    @classmethod
    def invoke(cls): ...
    @classmethod
    def on_del(cls, _: Any, uid: Any) -> None: ...
    def as_invocation(self): ...
    def as_call(self): ...
    def as_vim_function(self): ...

class expr_arg:
    arg: Any = ...
    def __init__(self, arg: str) -> None: ...

class AutoCmdGroup:
    name: Any = ...
    def __init__(self, name: Any) -> None: ...
    def __enter__(self): ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
    @staticmethod
    def delete_all() -> None: ...
    @staticmethod
    def add(event: Any, func: Any, *, pat: str = ..., once: bool = ..., nested: bool = ...) -> None: ...

def highlight(*, group: Optional[Any] = ..., clear: bool = ..., default: bool = ..., link: Optional[Any] = ..., disable: bool = ..., **kwargs: Any): ...
def error_msg(*args: Any) -> None: ...
def pedit(path: str, silent: Any=..., noerrors: Any=...) -> Any: ...
def feedkeys(keys: Any, mode: Optional[Any] = ..., literal: bool = ...) -> None: ...
def nmap(keys: Any, func: Any, curbuf: bool = ..., args: Any = ..., kwargs: Any = ...) -> None: ...
def timer_start(ms: Any, func: Any, **kwargs: Any): ...
def call_soon(func: Any) -> None: ...
def timer_stopall() -> None: ...
def popup_clear(force: bool = ...) -> None: ...
def find_buffer_by_name(name: str) -> Optional[buffers.Buffer]: ...

class saved_winview:
    view: dict
    def __enter__(self) -> None: ...
    def __exit__(self, *args: Any, **kwargs: Any) -> None: ...

vim: Vim
log: Log

class _Vim_desc:
    __doc_shadow__: Vim
    @property
    def buffers(self) -> Buffers: ...
    @property
    def windows(self) -> Windows: ...
    @property
    def tabpages(self) -> TabPages: ...
    @property
    def current(self) -> Current: ...
    @property
    def vars(self) -> Variables: ...
    @property
    def vvars(self) -> Variables: ...
    @property
    def options(self) -> GlobalOptions: ...
    def eval(expr: str) -> Union[dict, list, str]: ...
    def command(self, cmd: str) -> None: ...
