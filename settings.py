# -*- coding:utf-8 -*-
import os
import sys
import logging
import sublime
import sublime_plugin
from os.path import expanduser
from urllib.parse import urljoin


if sys.version_info[0] == 2:
    msg = "Sublimall is only available for SublimeText 3 (for now).\n Sorry about that."
    sublime.message_dialog(msg)
    for name, module in sys.modules.items():
        if name.startswith('sublimall'):
            sublime_plugin.unload_module(module)


logger = logging.getLogger('sublimall')
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(os.path.join(expanduser("~"), '.sublimall.log'))
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

API_ROOT_URL = 'http://localhost:8000'
API_UPLOAD_URL = urljoin(API_ROOT_URL, '/api/upload/')
API_RETRIEVE_URL = urljoin(API_ROOT_URL, '/api/retrieve/')
BACKUP_DIRECTORY_NAME = 'backups'
