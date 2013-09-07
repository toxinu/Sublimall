# -*- coding:utf-8 -*-
from urllib.parse import urljoin


API_ROOT_URL = 'http://www.sublimesync.org'
API_UPLOAD_URL = urljoin(API_ROOT_URL, '/api/upload/')
API_RETRIEVE_URL = urljoin(API_ROOT_URL, '/api/retrieve/')
BACKUP_DIRECTORY_NAME = 'backups'
