# -*- coding:utf-8 -*-
import os
import sys
import sublime
import sublime_plugin
import tarfile
from io import BytesIO
from .settings import API_RETRIEVE_URL
from .command import CommandWithStatus

sys.path.append(os.path.dirname(__file__))
import requests


class SublimeSyncRetrieveCommand(
        sublime_plugin.ApplicationCommand,
        CommandWithStatus):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncRetrieveCommand, self).__init__(*args, **kwargs)
        self.directory_list = None
        self.stream = None
        self.tf = None
        self.running = False

    def start(self):
        """
        Retrieve packages and uncompress them
        """
        self.running = True

        self.directory_list = [
            sublime.packages_path(),
            sublime.installed_packages_path()
        ]

        settings = sublime.load_settings('sublime-sync.sublime-settings')
        data = {
            'version': sublime.version()[:1],
            'username': settings.get('username', ''),
            'api_key': settings.get('api_key', ''),
        }

        self.set_message("Requesting archive...")
        response = requests.post(url=API_RETRIEVE_URL, data=data, stream=True)

        if response.status_code == 200:
            self.set_message("Downloading archive...")
            stream = BytesIO(response.raw.read())

            self.set_message("Extracting archive...")

            with tarfile.open(fileobj=stream, mode='r:gz') as tf:
                # Extract archive
                for directory in self.directory_list:
                    directory_basename = os.path.basename(os.path.normpath(directory))
                    members = [tarinfo for tarinfo in tf.getmembers() if tarinfo.name.startswith('%s' % directory_basename)]
                    for tarinfo in members:
                        try:
                            tf.extract(tarinfo, os.path.join(directory, os.path.pardir))
                        except IOError:
                            pass

            self.set_message("Your sublime has been synced !")
            stream.close()

        elif response.status_code == 403:
            self.set_message("Error while requesting archive: wrong credentials")

        elif response.status_code == 404:
            self.set_message("Error while requesting archive: version %s not found on remote" % sublime.version())

        self.unset_message()
        self.running = False

    def run(self, *args):
        if self.running:
            self.set_quick_message("Already working on a backup...")
            return
        sublime.set_timeout_async(self.start, 0)
