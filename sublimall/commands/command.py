# -*- coding:utf-8 -*-
import copy
import sublime


class MessageStatus(object):
    def __init__(self, message=""):
        self.is_running = False
        self.message = message
        self.previous_message = ""

    def set_message(self, message):
        self.previous_message = copy.deepcopy(self.message)
        self.message = message

    def run(self):
        sublime.status_message("[Sublimall] %s" % self.message)
        if self.is_running:
            sublime.set_timeout(lambda: self.run(), 100)


class CommandWithStatus(object):
    """
    This Command class allow you to control
    message status bar.
    """
    def __init__(self, *args, **kwargs):
        self._messageStatus = MessageStatus()
        sublime.set_timeout(lambda: self.unset_message, 3000)
        super().__init__(*args, **kwargs)

    def set_timed_message(self, message, time=7, clear=False):
        """
        Show a message for a specified amount of time
        and re-set the previous after it.
        """
        self.set_message(message)
        if not clear:
            sublime.set_timeout(
                lambda: self.set_message(self._messageStatus.previous_message),
                time * 1000)
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


class CommandWithHiddenPrompt(object):
    def __init__(self, *args, **kwargs):
        self.prompt_value = ''
        super().__init__(*args, **kwargs)

    def on_cancel_wrapper(self, *args, **kwargs):
        self.prompt_value = None
        return self.on_cancel_callback('', *args, **kwargs)

    def on_done_wrapper(self, *args, **kwargs):
        self.on_change_callback(*args, **kwargs)
        return self.on_done_callback(*args, **kwargs)

    def show_prompt(self, p=''):
        """
        Shows an input panel for entering password
        """
        self.view = sublime.active_window().show_input_panel(
            self.prompt_label,
            initial_text=p,
            on_done=self.on_done_wrapper,
            on_cancel=self.on_cancel_wrapper,
            on_change=self.on_change_callback
        )

    def on_change_callback(self, p):
        if p and len(p) != len(self.prompt_value):
            delta = len(self.prompt_value) - len(p)
            # Erase character
            if delta > 0:
                if delta > 1:
                    self.prompt_value = p[-1]
                else:
                    self.prompt_value = self.prompt_value[0:-delta]
            # Add character
            else:
                self.prompt_value += p[delta:]

            if self.view:
                self.view.close()
            self.show_prompt('*' * len(self.prompt_value))
        elif not p and (
                self.prompt_value is None or len(self.prompt_value) == 1):
            self.prompt_value = ''
            self.show_prompt()
        elif not p:
            self.prompt_value = ''
