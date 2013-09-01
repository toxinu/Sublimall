#-*- coding:utf-8 -*-
import os
import sys
import sublime
import sublime_plugin
import tarfile
import tempfile
from .settings import API_UPLOAD_URL

sys.path.append(os.path.dirname(__file__))
import requests


class SublimeSyncUploadCommand(sublime_plugin.ApplicationCommand):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncUploadCommand, self).__init__(*args, **kwargs)
        self.directory_list = None
        self.temp_filename = None
        self.tf = None

    def create_tarfile(self):
        """
        Create an temporary tarfile
        """
        _, self.temp_filename = tempfile.mkstemp(suffix='.tar.gz')
        return tarfile.open(self.temp_filename, mode="w:gz")

    def add_tarfile_directory(self, directory):
        """
        Add directory to the zipfile
        """
        self.tf.add(directory, arcname=os.path.basename(os.path.normpath(directory)))

    def send_to_api(self):
        """
        Send tar file to API
        """
        self.tf.close()

        settings = sublime.load_settings('sublime-sync.sublime-settings')
        files = {
            'package': open(self.temp_filename, 'rb'),
            'version': sublime.version()[:1],
            'username': settings.get('username', ''),
            'api_key': settings.get('api_key', ''),
        }

        response = requests.post(url=API_UPLOAD_URL, files=files)

        if response.status_code == 200:
            sublime.status_message(u"Successfuly sent archive")
        elif response.status_code == 403:
            sublime.status_message(u"Error while sending archive : wrong credentials")


        os.unlink(self.temp_filename)
        self.post_send()

    def post_send(self):
        self.temp_filename = None
        self.tf = None

    def run(self, *args):
        """
        Create a tar of all packages and settings
        """
        self.directory_list = [
            sublime.packages_path(),
            sublime.installed_packages_path()
        ]

        sublime.status_message(u"Creating archive...")
        self.tf = self.create_tarfile()

        for directory in self.directory_list:
            self.add_tarfile_directory(directory)

        sublime.status_message(u"Sending archive...")
        self.send_to_api()
