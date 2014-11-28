# -*- coding:utf-8 -*-
import os
import shutil
import sublime
from urllib.parse import urljoin
from sublime_plugin import ApplicationCommand

from .command import CommandWithStatus
from .command import CommandWithHiddenPrompt

from .. import requests
from .. import SETTINGS_USER_FILE
from ..logger import logger
from ..logger import show_report
from ..archiver import Archiver
from ..utils import humansize
from ..utils import get_headers


class UploadCommand(
        ApplicationCommand, CommandWithHiddenPrompt, CommandWithStatus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = False
        self.archive_filename = None
        self.view = None
        self.prompt_label = "Enter archive passphrase (will be hidden)"
        self.on_done_callback = self.pack_and_send_async
        self.on_cancel_callback = self.pack_and_send_async

    def post_send(self, clear=True):
        """
        Resets values
        """
        if clear:
            self.unset_message()
        self.running = False
        self.archive_filename = None
        self.prompt_value = ''

    def pack_and_send(self):
        """
        Create archive and send it to the API
        """
        self.set_message("Creating archive...")

        archiver = Archiver()
        try:
            self.archive_filename = archiver.pack_packages(
                password=self.prompt_value,
                exclude_from_package_control=self.exclude_from_package_control)
            if self.local_backup:
                shutil.copy(self.archive_filename, self.archives_path)
                self.set_timed_message(
                    "Archive successfully copied. Make a donation at "
                    "http://sublimall.org/donate !",
                    time=10,
                    clear=True)
                self.post_send()
            else:
                self.send_to_api()
        except Exception as err:
            msg = 'Error while creating archive'
            show_report(msg)
            self.set_timed_message(msg, clear=True)
            logger.error(err)
            self.post_send(clear=False)

    def pack_and_send_async(self, password=''):
        """
        Starts ansync command
        """
        sublime.set_timeout_async(self.pack_and_send, 0)

    def get_proxies(self):
        proxies = {}
        if self.settings.get('http_proxy', ''):
            proxies = {'http': self.settings.get('http_proxy')}
        return proxies

    def get_max_package_size(self):
        try:
            r = requests.post(
                self.api_max_package_size_url,
                headers=get_headers(),
                data={'email': self.email, 'api_key': self.api_key},
                proxies=self.get_proxies())
            if r.json().get('success'):
                return r.json().get('output')
            else:
                self.set_timed_message("Bad credentials.", clear=True)
                self.running = False
                logger.info('Bad credentials.')
        except Exception as err:
            self.set_timed_message(
                "Error while retrieving max package size.", clear=True)
            self.running = False
            logger.error(
                'Server: %s\n'
                '==========[EXCEPTION]==========\n'
                '%s\n'
                '===============================' % (
                    self.api_max_package_size_url, err))

    def send_to_api(self):
        """
        Send archive file to API
        """
        if not os.path.exists(self.archive_filename):
            msg = "Error while sending archive: archive not found."
            self.set_timed_message(msg)
            show_report(
                msg + '\n' + 'Path:%s' % self.archive_filename,
                exception=False)
            self.running = False
            return

        # Just get size
        f = open(self.archive_filename, 'rb')
        f.seek(0, 2)

        # Retrieve max package size
        package_size = f.tell()
        max_package_size = self.get_max_package_size()
        if max_package_size is None:
            self.running = False
            return
        if package_size > int(max_package_size):
            self.set_timed_message('Archive too big. %s instead of %s max.' % (
                humansize(package_size), humansize(max_package_size)))
            self.running = False
            return

        self.set_message("Sending archive (%s)..." % humansize(package_size))

        # Really open file
        f = open(self.archive_filename, 'rb')

        files = {
            'package': f.read(),
            'version': sublime.version()[:1],
            'platform': sublime.platform(),
            'arch': sublime.arch(),
            'email': self.email,
            'api_key': self.api_key,
        }

        # Send data and delete temporary file
        try:
            r = requests.post(
                url=self.api_upload_url,
                files=files,
                headers=get_headers(),
                proxies=self.get_proxies(),
                timeout=self.settings.get('http_upload_timeout'))
        except requests.exceptions.ConnectionError as err:
            self.set_timed_message(
                "Error while sending archive: server not available, try later",
                clear=True)
            self.running = False
            logger.error(
                'Server (%s) not available, try later.\n'
                '==========[EXCEPTION]==========\n'
                '%s\n'
                '===============================' % (
                    self.api_upload_url, err))
            return
        except requests.exceptions.Timeout as err:
            self.set_timed_message(
                "Error while sending archive: upload take to long time. "
                "Increase \"http_upload_timeout\" setting.",
                clear=True)
            self.running = False
            logger.error(
                'Server (%s) time out, request take too long, try later.\n'
                '==========[EXCEPTION]==========\n'
                '%s\n'
                '===============================' % (
                    self.api_upload_url, err))
            return
        except Exception as err:
            self.set_timed_message(
                "Error while sending archive\n", clear=True)
            self.running = False
            logger.error(
                'Server: %s\nHttp code: %s\n'
                '==========[EXCEPTION]==========\n'
                '%s\n'
                '===============================' % (
                    self.api_upload_url, r.status_code, err))
            return

        f.close()
        os.unlink(self.archive_filename)

        if r.status_code == 201:
            self.set_timed_message(
                "Successfully sent archive. Make a donation at "
                "http://sublimall.org/donate !",
                time=10,
                clear=True)
            logger.info('HTTP [%s] Successfully sent archive' % r.status_code)
        elif r.status_code == 403:
            self.set_timed_message(
                "Error while sending archive: wrong credentials", clear=True)
            logger.info('HTTP [%s] Bad credentials' % r.status_code)
        elif r.status_code == 413:
            self.set_timed_message(
                "Error while sending archive: filesize too large (>30MB)",
                clear=True)
            logger.error("HTTP [%s] %s" % (r.status_code, r.content))
        else:
            msg = "Unexpected error (HTTP STATUS: %s)" % r.status_code
            try:
                j = r.json()
                for error in j.get('errors'):
                    msg += " - %s" % error
            except:
                pass
            show_report('Unhandled Http error while uploading (%s).\n\n%s' % (
                r.status_code, r.content), exception=False)
            self.set_timed_message(msg, clear=True, time=10)
            logger.error('HTTP [%s] %s' % (r.status_code, r.content))

        self.post_send(clear=False)

    def run(self, *args):
        """
        Create an archive of all packages and settings
        """
        if self.running:
            self.set_timed_message("Already working on a backup...", time=1)
            logger.warn('Already working on a backup')
            return

        self.settings = sublime.load_settings(SETTINGS_USER_FILE)
        self.api_upload_url = urljoin(
            self.settings.get('api_root_url'),
            self.settings.get('api_upload_url'))
        self.api_max_package_size_url = urljoin(
            self.settings.get('api_root_url'),
            self.settings.get('api_max_package_size_url'))

        self.archives_path = self.settings.get('archives_path')
        self.local_backup = self.settings.get('local_backup')

        logger.info('Starting upload')

        self.email = self.settings.get('email', '')
        self.api_key = self.settings.get('api_key', '')
        self.exclude_from_package_control = self.settings.get(
            'exclude_from_package_control', False)
        self.encrypt = self.settings.get('encrypt', False)

        if not self.local_backup and (not self.email or not self.api_key):
            self.set_timed_message(
                "api_key or email is missing in your"
                " Sublimall configuration", clear=True)
            logger.warn(
                'API key or email is missing in configuration file. Abort')
            return

        self.running = True

        logger.info('Encrypt enabled')
        if self.encrypt:
            logger.info('Prompt archive passphrase')
            self.show_prompt()
        else:
            self.pack_and_send_async()
