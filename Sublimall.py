# -*- coding: utf-8 -*-
import os
import sys
import hashlib
import sublime
from imp import reload
from os.path import expanduser

st_version = 2
if int(sublime.version()) > 3000:
    st_version = 3

if st_version == 2:
    msg = "Sublimall is only available for SublimeText 3.\n Sorry about that."
    sublime.error_message(msg)

reloader_name = 'Sublimall.sublimall.reloader'
if reloader_name in sys.modules:
    print('******')
    reload(sys.modules[reloader_name])


def plugin_loaded():
    from .sublimall.utils import get_7za_bin

    if get_7za_bin() is None:
        msg = (
            "Sublimall needs 7zip to compress and encrypt "
            "your configuration.\n"
            "Please install it and specify its path in the settings file.")
        sublime.error_message(msg)

    arch_lib_path = None
    if sublime.platform() == 'linux':

        so_name = '_ssl.cpython-33m.so'
        arch_lib_path = os.path.join(
            'Packages',
            'Sublimall',
            'lib',
            'st%d_linux_%s' % (st_version, sublime.arch()))

        lib_dir_tmp = os.path.join(
            expanduser("~"),
            '.sublimall',
            'lib',
            'st%d_linux_%s' % (st_version, sublime.arch()))
        # If lib directory doesn't exist create it
        if not os.path.exists(lib_dir_tmp):
            os.makedirs(lib_dir_tmp)

        print('[Sublimall] enabling custom linux ssl module')
        for ssl_ver in ['1.0.0', '10', '0.9.8']:
            lib_path = os.path.join(arch_lib_path, 'libssl-' + ssl_ver)
            lib_path_tmp = os.path.join(lib_dir_tmp, 'libssl-' + ssl_ver)
            must_copy = False

            # If ssl specific version directory doesn't exist create it
            if not os.path.exists(lib_path_tmp):
                must_copy = True
                os.makedirs(lib_path_tmp)

            if not os.path.exists(
                    os.path.join(lib_path_tmp, so_name)):
                must_copy = True
            else:
                m = hashlib.md5()
                m.update(
                    sublime.load_binary_resource(
                        os.path.join(lib_path, so_name)))
                source_digest = m.hexdigest()
                m.update(open(os.path.join(lib_path_tmp, so_name), 'rb').read())
                dest_digest = m.hexdigest()
                if source_digest != dest_digest:
                    must_copy = True

            if must_copy:
                with open(os.path.join(lib_path_tmp, so_name), 'wb') as f:
                    f.write(sublime.load_binary_resource(
                        os.path.join(lib_path, so_name)))

            sys.path.append(lib_path_tmp)
            try:
                import _ssl
                sys.modules['ssl'] = sys.modules['_ssl']
                print(
                    '[Sublimall] successfully loaded _ssl '
                    'module for libssl.so.%s' % ssl_ver)
                break
            except (ImportError) as e:
                print('[Sublimall] _ssl module import error - ' + str(e))
        if '_ssl' in sys.modules:
            try:
                import ssl
            except (ImportError) as e:
                print('[Sublimall] ssl module import error - ' + str(e))

        # SSL Monkey patch for Linux
        import http.client
        reload(http.client)

from .sublimall import reloader
from .sublimall.commands import *
