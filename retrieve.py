# -*- coding:utf-8 -*-
import os
import sys
import time
import shutil
import sublime
import zipfile
import sublime_plugin
from .archiver import Archiver
from .command import CommandWithStatus
from .settings import API_RETRIEVE_URL, BACKUP_DIRECTORY_NAME
from .utils import generate_temp_filename

sys.path.append(os.path.dirname(__file__))
import requests


class SublimeSyncRetrieveCommand(sublime_plugin.ApplicationCommand, CommandWithStatus):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncRetrieveCommand, self).__init__(*args, **kwargs)
        self.stream = None
        self.running = False
        self.password = None
        self.archive_filename = None

    def post_unpack(self):
        """
        Resets values
        """
        self.unset_message()
        os.unlink(self.archive_filename)
        self.stream = None
        self.running = False
        self.password = None
        self.archive_filename = None

    def abort(self):
        """
        Aborts unpacking
        """
        self.set_message("No password supplied : aborting.")
        self.post_unpack()

    def prompt_password(self):
        """
        Shows an input panel for entering password
        """
        sublime.active_window().show_input_panel(
            "Enter archive password",
            initial_text='',
            on_done=self.check_zipfile,
            on_cancel=self.abort,
            on_change=None
        )

    def check_zipfile(self, password=None, first_try=False):
        """
        Check if stream is an unprotected zipfile
        If retry set to True, loop one more time
        """
        # Try opening the zipfile to check password
        try:
            if password is not None:
                self.zf.setpassword(password.encode())
            self.zf.testzip()
        except RuntimeError:
            if first_try:
                self.set_message("Archive is protected. Please enter password.")
            else:
                self.set_message("Wrong password")
            self.prompt_password()
        else:
            self.password = password
            self.zf.close()
            sublime.set_timeout_async(self.unpack, 0)

    def retrieve_from_server(self):
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

            # Create a temporary file and write response content in it
            self.archive_filename = generate_temp_filename()
            self.stream = open(self.archive_filename, 'wb')
            shutil.copyfileobj(response.raw, self.stream)
            self.stream.close()

            # Had some mysterious problems using in memory stream so re-open file instead
            self.zf = zipfile.ZipFile(self.archive_filename, 'r')
            self.check_zipfile(first_try=True)

        elif response.status_code == 403:
            self.set_message("Error while requesting archive: wrong credentials")

        elif response.status_code == 404:
            self.set_message("Error while requesting archive: version %s not found on remote" % sublime.version())

    def backup(self):
        """
        Creates a backup of Packages and Installed Packages before unpacking
        """
        archiver = Archiver()
        archiver.pack_packages(output_filename=os.path.join(os.path.dirname(__file__), BACKUP_DIRECTORY_NAME, '%s.zip' % time.time()))

    def unpack(self):
        """
        Unpack archive
        """
        self.backup()

        # Move pacakges directories to a .bak
        self.set_message(u"Moving directories...")
        archiver = Archiver()
        archiver.move_packages_to_backup_dirs()

        # Unpack backup
        self.set_message(u"Extracting archive...")
        archiver.unpack_packages(self.archive_filename, password=self.password)

        # Delete moved directories
        self.set_message(u"Deleting old directories...")
        archiver.remove_backup_dirs()

        self.set_message(u"Your Sublime Text has been synced !")
        self.post_unpack()

    def start(self):
        """
        Decrypt stream using private key
        """
        self.running = True

        settings = sublime.load_settings('sublime-sync.sublime-settings')

        self.username = settings.get('username', '')
        self.api_key = settings.get('api_key', '')

        self.retrieve_from_server()

    def run(self, *args):
        if self.running:
            self.set_quick_message("Already working on a backup...")
            return
        sublime.set_timeout_async(self.start, 0)
