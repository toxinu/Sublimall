# -*- coding: utf-8 -*-
import sys
import sublime
from imp import reload

if sys.version_info.major == 2:
    msg = "Sublimall is only available for SublimeText 3.\n Sorry about that."
    sublime.error_message(msg)

reloader_name = 'Sublimall.sublimall.reloader'
if reloader_name in sys.modules:
    reload(sys.modules[reloader_name])


def plugin_loaded():
    from .sublimall.utils import get_7za_bin

    if get_7za_bin() is None:
        msg = (
            "Sublimall needs 7zip to compress and encrypt your configuration.\n"
            "Please install it and specify its path in the settings file.")
        sublime.error_message(msg)

from .sublimall import reloader
from .sublimall.commands import *
