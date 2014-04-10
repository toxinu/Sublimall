#-*- coding:utf-8 -*-
import os
import sublime
from datetime import datetime

from sublime_plugin import ApplicationCommand

from .command import CommandWithStatus

from ..archiver import Archiver
from .. import SETTINGS_USER_FILE


class RestoreCommand(ApplicationCommand, CommandWithStatus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = False

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

            self.set_message(u"Your Sublime Text has been restored !")
            self.unset_message()
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
        self.backups = []

        for f in os.listdir(self.backup_path):
            if os.path.isfile(os.path.join(self.backup_path, f)):
                try:
                    d = self.datetime_from_filename(f)
                    self.backups.append(['Backup on %s' % d.strftime('%c'), f])
                except Exception:
                    pass

        self.backups.sort(
            key=lambda item: self.datetime_from_filename(item[1]), reverse=True)

    def start(self):
        """
        Restores a backup
        """
        self.get_backups()

        if self.backups:
            self.running = True
            sublime.active_window().show_quick_panel(self.backups, self.restore)
        else:
            self.set_message("No backups found")
            self.unset_message()

    def run(self, *args):
        if self.running:
            self.set_timed_message("Already working on a restore...")
            return

        self.settings = sublime.load_settings(SETTINGS_USER_FILE)

        self.backups = []
        self.backup_path = os.path.join(sublime.packages_path(), 'Sublimall', 'Backup')

        sublime.set_timeout_async(self.start, 0)
