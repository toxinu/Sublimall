# -*- coding:utf-8 -*-
import os
import time
import sublime
import logging
import tempfile
import platform
import traceback
from os.path import expanduser

from . import __version__


report_footer = """\n
SublimeText version: {sublime_version}
7za path: {bin_7za}
Sublimall version: {sublimall_version}
Operating System: {operating_system}\n\n
Sorry about this error, you could find some help on:
- Github: https://github.com/socketubs/Sublimall/issues
- Doc: http://sublimall.org/docs
- Log file: ~/.sublimall.log
- SublimeText console
Or maybe open an issue.

Socketubs."""

logger = logging.getLogger('sublimall')
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(os.path.join(expanduser("~"), '.sublimall.log'))
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def get_report_path():
    report_id = 0
    now = time.strftime("%Y%m%d-%H%M%S")
    report_path = None
    while not report_path:
        p = os.path.join(tempfile.gettempdir(), 'sublimall-%s-%s.log' % (
            now, report_id))
        if not os.path.exists(p):
            report_path = p
        else:
            report_id += 1
    return report_path


def show_report(subtitle, message=None, exception=True):
    from .utils import get_7za_bin

    report_path = get_report_path()
    with open(report_path, 'w') as f:
        title = "Sublimall error report"
        title += "\n" + "#" * len(title) + "\n\n"
        f.write(title)

        f.write('%s\n' % subtitle)
        if message:
            f.write(message)
        if exception:
            f.write('\n')
            f.write(
                '=' * 35 + ' Traceback ' +
                '=' * 35 + '\n' + traceback.format_exc())
            f.write('=' * 81 + '\n')

        f.write(report_footer.format(
            sublime_version=sublime.version(),
            bin_7za=get_7za_bin(),
            sublimall_version=__version__,
            operating_system=platform.platform()))
    sublime.active_window().open_file(report_path)
