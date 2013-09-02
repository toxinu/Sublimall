#-*- coding:utf-8 -*-
import os
import sys
import shutil
import sublime
import sublime_plugin
import zipfile
from io import BytesIO
from .settings import API_RETRIEVE_URL

sys.path.append(os.path.dirname(__file__))
import requests
from rsa.bigfile import decrypt_bigfile
import rsa


class SublimeSyncRetrieveCommand(sublime_plugin.ApplicationCommand):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncRetrieveCommand, self).__init__(*args, **kwargs)
        self.directory_list = None
        self.out_stream = None
        self.stream = None
        self.zf = None

    def decrypt_stream(self):
        """
        Decrypt stream using private key
        """
        sublime.status_message(u"Decrypting archive...")

        with open('keys/sublimesync', 'rb') as privatekey_file:
            keydata = privatekey_file.read()
        private_key = rsa.PrivateKey.load_pkcs1(keydata)

        self.out_stream = BytesIO()
        decrypt_bigfile(self.stream, self.out_stream, private_key)
        self.out_stream.seek(0)

    def unpack(self):
        """
        Unpack archive to packages folders
        """
        sublime.status_message(u"Extracting archive...")

        # Extract archive
        with zipfile.ZipFile(self.out_stream, 'r') as zf:
            for directory in self.directory_list:
                directory_basename = os.path.basename(os.path.normpath(directory))
                members = [zipinfo for zipinfo in zf.infolist() if zipinfo.filename.startswith('%s' % directory_basename)]
                for zipinfo in members:
                    try:
                        zf.extract(zipinfo, os.path.join(directory, os.path.pardir))
                    except IOError as e:
                        print(e)
                        pass

        self.post_unpack()

    def post_unpack(self):
        self.stream.close()
        self.out_stream.close()

    def retrieve_from_api(self):
        """
        Retrieve archive from API
        """
        data = {
            'version': sublime.version()[:1],
            'username': self.username,
            'api_key': self.api_key,
        }

        sublime.status_message(u"Requesting archive...")
        response = requests.post(url=API_RETRIEVE_URL, data=data, stream=True)

        if response.status_code == 200:
            sublime.status_message(u"Downloading archive...")
            self.stream = BytesIO(response.raw.read())
            self.decrypt_stream()
            self.unpack()

        elif response.status_code == 403:
            sublime.status_message(u"Error while requesting archive : wrong credentials")

        elif response.status_code == 404:
            sublime.status_message(u"Error while requesting archive : version %s not found on remote" % sublime.version())


    def run(self, *args):
        """
        Retrieve packages and uncompress them
        """
        self.directory_list = [
            sublime.packages_path(),
            sublime.installed_packages_path()
        ]

        settings = sublime.load_settings('sublime-sync.sublime-settings')

        self.username = settings.get('username', '')
        self.api_key = settings.get('api_key', '')

        self.retrieve_from_api()
