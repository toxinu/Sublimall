# -*- coding:utf-8 -*-
import os
import uuid
import shutil
import sublime
import tempfile

from . import SETTINGS_USER_FILE


def get_7za_bin():
    settings = sublime.load_settings(SETTINGS_USER_FILE)
    return shutil.which('7za') or settings.get('7za_path', None)


def generate_temp_filename():
    return os.path.join(tempfile.gettempdir(), 'sublime-sync_%s.zip' % str(uuid.uuid4()))


def copytree(src, dst, symlinks=False):
    names = os.listdir(src)
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks)
            else:
                shutil.copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except OSError as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except shutil.WindowsError:
        # can't copy file access times on Windows
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise Error(errors)