# -*- coding:utf-8 -*-
import sublime


class MessageStatus(object):
    def __init__(self, message=""):
        self.is_running = False
        self.message = message

    def set_message(self, message):
        self.message = message

    def run(self):
        sublime.status_message(self.message)
        if self.is_running:
            sublime.set_timeout(lambda: self.run(), 100)
