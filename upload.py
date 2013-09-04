#-*- coding:utf-8 -*-
import os
import sys
import sublime
import sublime_plugin
import zipfile
import tempfile
from io import BytesIO
from .crypt import Crypto
from .settings import API_UPLOAD_URL

sys.path.append(os.path.dirname(__file__))
import requests


class SublimeSyncUploadCommand(sublime_plugin.ApplicationCommand):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncUploadCommand, self).__init__(*args, **kwargs)
        self.directory_list = None
        self.temp_filename = None
        self.out_stream = None
        self.stream = None
        self.pwd = None
        self.zf = None

    def pack_and_send(self):
        """
        Create archive and send it to the API
        """
        self.directory_list = [
            sublime.packages_path(),
            sublime.installed_packages_path()
        ]

        sublime.status_message(u"Creating archive...")

        self.zf = self.create_archive()

        for directory in self.directory_list:
            self.add_archive_directory(directory)

        self.zf.close()
        self.stream.seek(0)

        if self.encrypt:
            self.input_password()
        else:
            self.send_to_api()

    def create_archive(self):
        """
        Create an in memory archive
        """
        self.stream = BytesIO()
        return zipfile.ZipFile(self.stream, mode='w', compression=zipfile.ZIP_DEFLATED)

    def add_archive_directory(self, directory):
        """
        Add directory to the archive
        """
        for root, dirs, files in os.walk(directory):
            for name in files:
                filename = os.path.join(root, name)
                if not filename.startswith(os.path.dirname(os.path.realpath(__file__))):
                    self.zf.write(
                        filename=filename,
                        arcname=os.path.relpath(filename, os.path.dirname(directory))
                    )

    def input_password(self):
        """
        Show an input panel for entering password
        """
        sublime.active_window().show_input_panel(
            "Enter archive password",
            initial_text='',
            on_done=self.encrypt_stream,
            on_cancel=self.send_to_api,
            on_change=None
        )

    def encrypt_stream(self, password):
        """
        Encrypt stream using public key
        """
        self.out_stream = Crypto(self.stream).encrypt_data(password=password)
        self.send_to_api()

    def send_to_api(self):
        """
        Send archive file to API
        """
        sublime.status_message(u"Sending archive...")

        if self.out_stream is None:
            self.out_stream = self.stream

        files = {
            'package': self.out_stream.read(),
            'version': sublime.version()[:1],
            'username': self.username,
            'api_key': self.api_key,
        }

        response = requests.post(url=API_UPLOAD_URL, files=files)

        if response.status_code == 200:
            sublime.status_message(u"Successfuly sent archive")
        elif response.status_code == 403:
            sublime.status_message(u"Error while sending archive : wrong credentials")

        self.post_send()

    def post_send(self):
        self.stream.close()
        self.out_stream.close()
        self.temp_filename = None
        self.out_stream = None
        self.stream = None
        self.zf = None

    def run(self, *args):
        """
        Create an archive of all packages and settings
        """
        settings = sublime.load_settings('sublime-sync.sublime-settings')

        self.username = settings.get('username', '')
        self.api_key = settings.get('api_key', '')
        self.encrypt = settings.get('encrypt', False)

        self.pack_and_send()
