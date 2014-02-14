# -*- coding: utf-8 -*-
import sys
import sublime
from imp import reload
from .sublimall.utils import get_7za_bin

reloader_name = 'Sublimall.sublimall.reloader'
if reloader_name in sys.modules:
    reload(sys.modules[reloader_name])

load_sublimall = True
settings = sublime.load_settings('Sublimall.sublime-settings')
if sys.version_info.major == 2:
    msg = "Sublimall is only available for SublimeText 3.\n Sorry about that."
    sublime.error_message(msg)
    load_sublimall = False
if get_7za_bin() is None:
    msg = "Sublimall need 7zip to archive and encrypt your configuration.\nInstall it. "
    sublime.error_message(msg)
    load_sublimall = False

if load_sublimall:
    from .sublimall import reloader
    from .sublimall.commands import *
