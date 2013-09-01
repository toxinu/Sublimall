#-*- coding:utf-8 -*-
from urllib.parse import urljoin


API_ROOT_URL = 'http://sublimesync.florianpaquet.com/'
API_UPLOAD_URL = urljoin(API_ROOT_URL, '/upload/')
API_RETRIEVE_URL = urljoin(API_ROOT_URL, '/retrieve/')