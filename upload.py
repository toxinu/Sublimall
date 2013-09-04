# -*- coding:utf-8 -*-
import os
import sys
import sublime
import sublime_plugin
import tarfile
import tempfile
from .settings import API_UPLOAD_URL
from .command import CommandWithStatus

sys.path.append(os.path.dirname(__file__))
import requests


class SublimeSyncUploadCommand(sublime_plugin.ApplicationCommand, CommandWithStatus):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncUploadCommand, self).__init__(*args, **kwargs)
        self.directory_list = None
        self.temp_filename = None
        self.tf = None
        self.running = False

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
        self.tf.add(
            name=directory,
            arcname=os.path.basename(os.path.normpath(directory)),
            exclude=lambda filename: filename.startswith(os.path.dirname(os.path.realpath(__file__)))
        )

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
            'api_key': settings.get('api_key', '')
        }

        response = requests.post(url=API_UPLOAD_URL, files=files)

        if response.status_code == 200:
            self.set_message("Successfuly sent archive")
        elif response.status_code == 403:
            self.set_message("Error while sending archive: wrong credentials")

        os.unlink(self.temp_filename)
        self.post_send()

    def post_send(self):
        self.temp_filename = None
        self.tf = None

    def start(self):
        """
        Create a tar of all packages and settings
        """
        self.running = True
        self.set_message("Creating archive...")

        self.directory_list = [
            sublime.packages_path(),
            sublime.installed_packages_path()
        ]

        self.tf = self.create_tarfile()

        for directory in self.directory_list:
            self.add_tarfile_directory(directory)

        self.set_message("Sending archive...")
        self.send_to_api()

        self.unset_message()
        self.running = False

    def run(self, *args):
        if self.running:
            self.set_quick_message("Already working on a backup...")
            return
        sublime.set_timeout_async(self.start, 0)
