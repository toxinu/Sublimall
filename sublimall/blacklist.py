# -*- coding:utf-8 -*-
import sublime
from . import SETTINGS_USER_FILE

# Path: Packages/
packages = [
    'Sublimall', ]

# Path: Installed Packages/
installed_packages = [
    'Sublimall.sublime-package', ]


def get_ignored_packages():
    __settings = sublime.load_settings(SETTINGS_USER_FILE)
    custom_packages = []
    for ignored_package in __settings.get('ignore_packages', []):
        custom_packages.append(ignored_package)
    return custom_packages
