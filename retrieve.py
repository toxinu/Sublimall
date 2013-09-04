# -*- coding:utf-8 -*-
import os
import sys
import sublime
import sublime_plugin
import zipfile
from io import BytesIO
from .crypt import Crypto
from .settings import API_RETRIEVE_URL
from .command import CommandWithStatus

sys.path.append(os.path.dirname(__file__))
import requests


class SublimeSyncRetrieveCommand(sublime_plugin.ApplicationCommand, CommandWithStatus):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncRetrieveCommand, self).__init__(*args, **kwargs)
        self.directory_list = None
        self.out_stream = None
        self.password = None
        self.running = False
        self.stream = None
        self.zf = None

    def abort(self):
        self.set_message(u"No password supplied : aborting")
        self.post_unpack()

    def input_password(self):
        """
        Show an input panel for entering password
        """
        sublime.active_window().show_input_panel(
            "Enter archive password",
            initial_text='',
            on_done=self.pre_decrypt_stream,
            on_cancel=self.abort,
            on_change=None
        )

    def pre_decrypt_stream(self, password):
        """
        Start an decryption thread
        """
        self.password = password
        self.set_message("Decrypting archive...")
        sublime.set_timeout_async(self.decrypt_stream, 0)

    def decrypt_stream(self):
        self.out_stream = Crypto(self.stream).decrypt_data(password=self.password)
        try:
            self.zf = zipfile.ZipFile(self.out_stream, 'r')
            self.unpack()
        except zipfile.BadZipfile:
            self.set_message(u"Wrong password : aborting")
            self.post_unpack()

    def unpack(self):
        """
        Unpack archive to packages folders
        """
        # Extract archive
        for directory in self.directory_list:
            directory_basename = os.path.basename(os.path.normpath(directory))
            members = [zipinfo for zipinfo in self.zf.infolist() if zipinfo.filename.startswith(directory_basename)]
            for zipinfo in members:
                try:
                    self.zf.extract(zipinfo, os.path.join(directory, os.path.pardir))
                except IOError:
                    pass

        self.set_message(u"Your Sublime has been synced !")
        self.post_unpack()

    def post_unpack(self):
        self.unset_message()
        self.stream.close()
        self.password = None
        self.running = False
        if self.out_stream is not None:
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

        self.set_message("Requesting archive...")
        response = requests.post(url=API_RETRIEVE_URL, data=data, stream=True)

        if response.status_code == 200:
            self.set_message(u"Downloading archive...")
            self.stream = BytesIO(response.raw.read())

            self.set_message(u"Unpacking...")
            try:
                self.zf = zipfile.ZipFile(self.stream, 'r')
                self.unpack()
            except zipfile.BadZipfile:
                self.input_password()

        elif response.status_code == 403:
            self.set_message("Error while requesting archive: wrong credentials")
        elif response.status_code == 404:
            self.set_message("Error while requesting archive: version %s not found on remote" % sublime.version())

    def start(self):
        """
        Decrypt stream using private key
        """
        self.running = True

        self.directory_list = [
            sublime.packages_path(),
            sublime.installed_packages_path()
        ]

        settings = sublime.load_settings('sublime-sync.sublime-settings')

        self.username = settings.get('username', '')
        self.api_key = settings.get('api_key', '')

        self.retrieve_from_api()

    def run(self, *args):
        if self.running:
            self.set_quick_message("Already working on a backup...")
            return
        sublime.set_timeout_async(self.start, 0)
