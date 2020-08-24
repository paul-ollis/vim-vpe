"""Mypy stub."""
from __future__ import annotations

from typing import Optional, Callable, Any, Tuple, Dict, Union, Callable, List

import vim as _vim

from . import core_gen

VimError = core_gen.VimError
Log = core_gen.Log
Timer = core_gen.Timer
_PopupOption = core_gen._PopupOption
_PopupROOption = core_gen._PopupROOption
_PopupWOOption = core_gen._PopupWOOption
_PopupRWOption = core_gen._PopupRWOption
_PopupROPos = core_gen._PopupROPos
_PopupWOPos = core_gen._PopupWOPos
_PopupRWPos = core_gen._PopupRWPos
Popup = core_gen.Popup
PopupAtCursor = core_gen.PopupAtCursor
PopupBeval = core_gen.PopupBeval
PopupNotification = core_gen.PopupNotification
PopupDialog = core_gen.PopupDialog
PopupMenu = core_gen.PopupMenu
Function = core_gen.Function
Registers = core_gen.Registers
Callback = core_gen.Callback
expr_arg = core_gen.expr_arg
AutoCmdGroup = core_gen.AutoCmdGroup
highlight = core_gen.highlight
error_msg = core_gen.error_msg
pedit = core_gen.pedit
feedkeys = core_gen.feedkeys
nmap = core_gen.nmap
timer_start = core_gen.timer_start
call_soon = core_gen.call_soon
timer_stopall = core_gen.timer_stopall
popup_clear = core_gen.popup_clear
find_buffer_by_name = core_gen.find_buffer_by_name
saved_winview = core_gen.saved_winview
vim = core_gen.vim
log = core_gen.log


class Vim(core_gen.Vim):

    def getpos(self, expr: str) -> List[int]: ...
