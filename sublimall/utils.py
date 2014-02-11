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
