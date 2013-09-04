#-*- coding:utf-8 -*-
import os
import sys
import shutil
import sublime
import sublime_plugin
import zipfile
from io import BytesIO
from .crypt import Crypto
from .settings import API_RETRIEVE_URL

sys.path.append(os.path.dirname(__file__))
import requests


class SublimeSyncRetrieveCommand(sublime_plugin.ApplicationCommand):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncRetrieveCommand, self).__init__(*args, **kwargs)
        self.directory_list = None
        self.out_stream = None
        self.stream = None
        self.zf = None

    def decrypt_stream(self, password):
        """
        Decrypt stream using private key
        """
        self.out_stream = Crypto(self.stream).decrypt_data(password=password)
        try:
            self.zf = zipfile.ZipFile(self.out_stream, 'r')
            self.unpack()
        except zipfile.BadZipfile:
            sublime.status_message(u"Wrong password : aborting")

    def abort(self):
        sublime.status_message(u"No password supplied : aborting")

    def input_password(self):
        """
        Show an input panel for entering password
        """
        sublime.active_window().show_input_panel(
            "Enter archive password",
            initial_text='',
            on_done=self.decrypt_stream,
            on_cancel=self.abort,
            on_change=None
        )

    def unpack(self):
        """
        Unpack archive to packages folders
        """
        sublime.status_message(u"Extracting archive...")

        # Extract archive
        for directory in self.directory_list:
            directory_basename = os.path.basename(os.path.normpath(directory))
            members = [zipinfo for zipinfo in self.zf.infolist() if zipinfo.filename.startswith(directory_basename)]
            for zipinfo in members:
                try:
                    self.zf.extract(zipinfo, os.path.join('/home/florian/tmp/unpack/', os.path.pardir))
                    #self.zf.extract(zipinfo, os.path.join(directory, os.path.pardir))
                except IOError:
                    pass

        self.post_unpack()

    def post_unpack(self):
        self.stream.close()
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

        sublime.status_message(u"Requesting archive...")
        response = requests.post(url=API_RETRIEVE_URL, data=data, stream=True)

        if response.status_code == 200:
            sublime.status_message(u"Downloading archive...")
            self.stream = BytesIO(response.raw.read())

            try:
                self.zf = zipfile.ZipFile(self.stream, 'r')
                self.unpack()
            except zipfile.BadZipfile:
                self.input_password()

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
