#-*- coding:utf-8 -*-
import os
import sublime
import sublime_plugin
from datetime import datetime
from .archiver import Archiver
from .command import CommandWithStatus
from .settings import BACKUP_DIRECTORY_NAME


class SublimeSyncRestore(sublime_plugin.ApplicationCommand, CommandWithStatus):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncRestore, self).__init__(*args, **kwargs)
        self.running = False
        self.backups = []
        self.backup_path = os.path.join(os.path.dirname(__file__), BACKUP_DIRECTORY_NAME)

    def restore(self, index):
        """
        Starts restore process
        """
        if index != -1:
            backup = self.backups[index]

            # Move pacakges directories to a .bak
            self.set_message(u"Moving directories...")
            archiver = Archiver()
            archiver.move_packages_to_backup_dirs()

            # Unpack backup
            self.set_message(u"Unpacking backup...")
            archiver.unpack_packages(os.path.join(self.backup_path, backup[1]))

            # Delete moved directories
            self.set_message(u"Deleting old directories...")
            archiver.remove_backup_dirs()

            self.set_message(u"Yout Sublime Text has been restored !")
            self.running = False

    def datetime_from_filename(self, filename):
        """
        Returns a datetime object from a filename with timestamp
        """
        return datetime.fromtimestamp(float(os.path.splitext(filename)[0]))

    def get_backups(self):
        """
        Retrieves a list of backup archives
        """
        self.backups = [['Backup on %s' % self.datetime_from_filename(f).strftime('%c'), f]
                        for f in os.listdir(self.backup_path) if os.path.isfile(os.path.join(self.backup_path, f))]
        self.backups.sort(key=lambda item: self.datetime_from_filename(item[1]), reverse=True)

    def start(self):
        """
        Restores a backup
        """
        self.running = True
        self.get_backups()
        sublime.active_window().show_quick_panel(self.backups, self.restore)

    def run(self, *args):
        if self.running:
            self.set_quick_message("Already working on a restore...")
            return
        sublime.set_timeout_async(self.start, 0)
