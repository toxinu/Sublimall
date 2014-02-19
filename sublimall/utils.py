# -*- coding:utf-8 -*-
import os
import uuid
import shutil
import sublime
import tempfile
from . import SETTINGS_USER_FILE


def get_7za_bin():
    settings = sublime.load_settings(SETTINGS_USER_FILE)
    zip_bin = None

    if settings.get('7za_path') and os.path.exists(settings.get('7za_path')):
        zip_bin = settings.get('7za_path')
    elif shutil.which('7z'):
        zip_bin = shutil.which('7z')
    elif shutil.which('7za'):
        zip_bin = shutil.which('7za')
    elif os.name == 'nt':
        if os.path.exists(os.path.join(os.environ.get('ProgramFiles'), '7-Zip', '7z.exe')):
            zip_bin = os.path.join(os.environ.get('ProgramFiles'), '7-Zip', '7z.exe')
        if os.path.exists(os.path.join(os.environ.get('ProgramFiles(x86)'), '7-Zip', '7z.exe')):
            zip_bin = os.path.join(os.environ.get('ProgramFiles(x86)'), '7-Zip', '7z.exe')

    return zip_bin


def generate_temp_filename():
    return os.path.join(tempfile.gettempdir(), 'sublime-sync_%s.zip' % str(uuid.uuid4()))
