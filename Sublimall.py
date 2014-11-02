# -*- coding: utf-8 -*-
import os
import sys
import imp
import sublime
from imp import reload

st_version = 2
if int(sublime.version()) > 3000:
    st_version = 3

if st_version == 2:
    msg = "Sublimall is only available for SublimeText 3.\n Sorry about that."
    sublime.error_message(msg)

if sublime.platform() == 'linux':
    so_name = '_ssl.cpython-33m.so'
    arch_lib_path = os.path.join(
        os.path.dirname(__file__),
        'lib',
        'st%d_linux_%s' % (st_version, sublime.arch()))

    print('[Sublimall] enabling custom linux ssl module')
    for ssl_ver in ['1.0.0', '10', '0.9.8']:
        lib_path = os.path.join(arch_lib_path, 'libssl-' + ssl_ver)
        sys.path.append(lib_path)
        try:
            import _ssl
            print(
                '[Sublimall] successfully loaded _ssl '
                'module for libssl.so.%s' % ssl_ver)
            import http.client
            imp.reload(http.client)
            break
        except (ImportError) as e:
            print('[Sublimall] _ssl module import error - ' + str(e))
    if '_ssl' in sys.modules:
        try:
            import ssl
        except (ImportError) as e:
            print('[Sublimall] ssl module import error - ' + str(e))

reloader_name = 'Sublimall.sublimall.reloader'
if reloader_name in sys.modules:
    reload(sys.modules[reloader_name])


def plugin_loaded():
    from .sublimall.utils import get_7za_bin

    if get_7za_bin() is None:
        msg = (
            "Sublimall needs 7zip to compress and encrypt "
            "your configuration.\n"
            "Please install it and specify its path in the settings file.")
        sublime.error_message(msg)

from .sublimall import reloader
from .sublimall.commands import *
