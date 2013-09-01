#-*- coding:utf-8 -*-
from urllib.parse import urljoin


API_ROOT_URL = 'http://192.168.1.10:8000/'
API_UPLOAD_URL = urljoin(API_ROOT_URL, '/upload/')
API_RETRIEVE_URL = urljoin(API_ROOT_URL, '/retrieve/')
