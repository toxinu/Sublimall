# -*- coding:utf-8 -*-
import os
import logging
from os.path import expanduser
from urllib.parse import urljoin

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
