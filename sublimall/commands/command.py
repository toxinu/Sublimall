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


class CommandWithStatus(object):
    """
    This Command class allow you to control
    message status bar.
    """
    def __init__(self, *args, **kwargs):
        self._messageStatus = MessageStatus()
        sublime.set_timeout(lambda: self.unset_message, 1000)

    def set_timed_message(self, message, time=5, clear=False):
        """
        Show a message for a specified amount of time
        and re-set the previous after it.
        """
        old_message = self._messageStatus.message
        self.set_message(message)
        if not clear:
            sublime.set_timeout(lambda: self.set_message(old_message), time * 1000)
        else:
            self.unset_message()

    def set_message(self, message):
        """ Set a message """
        self._messageStatus.set_message(message)
        if not self._messageStatus.is_running:
            self._messageStatus.is_running = True
            self._messageStatus.run()

    def unset_message(self):
        """
        Unset message and stop refreshing
        status message bar.
        """
        self._messageStatus.is_running = False
