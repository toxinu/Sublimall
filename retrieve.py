#-*- coding:utf-8 -*-
import os
import sys
import sublime
import sublime_plugin
import tarfile
from io import BytesIO
from settings import API_RETRIEVE_URL

sys.path.append(os.path.dirname(__file__))
import requests


class SublimeSyncRetrieveCommand(sublime_plugin.ApplicationCommand):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncRetrieveCommand, self).__init__(*args, **kwargs)
        self.stream = None
        self.tf = None

    def run(self, *args):
        """
        Retrieve packages and uncompress them
        """
        settings = sublime.load_settings('sublime-sync.sublime-settings')
        data = {
            'version': sublime.version()[:1],
            'username': settings.get('username', ''),
            'api_key': settings.get('api_key', ''),
        }

        sublime.status_message(u"Requesting archive...")
        response = requests.post(url=API_RETRIEVE_URL, data=data, stream=True)

        if response.status_code == 200:
            sublime.status_message(u"Downloading archive...")
            stream = BytesIO(response.raw.read())

            sublime.status_message(u"Extracting archive...")

            with tarfile.open(fileobj=stream, mode='r:gz') as tf:
                # Extract archive
                for directory in [sublime.packages_path(), sublime.installed_packages_path()]:
                    directory_basename = os.path.basename(os.path.normpath(directory))
                    tf.extractall(os.path.join(directory, os.path.pardir), [tarinfo for tarinfo in tf.getmembers() if tarinfo.name.startswith('%s/' % directory_basename)])

            sublime.status_message(u"Your sublime has been synced !")
            stream.close()

        elif response.status_code == 403:
            sublime.status_message(u"Error while requesting archive : wrong credentials")

        elif response.status_code == 404:
            sublime.status_message(u"Error while requesting archive : version %s not found on remote" % sublime.version())
