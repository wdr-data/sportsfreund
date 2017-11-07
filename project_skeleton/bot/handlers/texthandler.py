
import re
import threading

from .handler import Handler


class TextHandler(Handler):
    """
    Handler class to handle text messages. It uses a regular expression to check text messages.

    Attributes:
        callback (:obj:`callable`): The callback function for this handler.
        pattern (:obj:`str` | :obj:`Pattern`): The regex pattern.

    Args:
        callback (:obj:`callable`): A function that takes ``bot, event`` as positional arguments.
            It will be called when the :attr:`check_event` has determined that an event should be
            processed by this handler.
        pattern (:obj:`str` | :obj:`Pattern`): The regex pattern.

    """

    def __init__(self, callback, pattern=None):
        super().__init__(callback)

        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        self.pattern = pattern

        # We use this to carry data from check_event to handle_event in multi-threaded environments
        self.local = threading.local()

    def check_event(self, event):
        """
        Determines whether an event should be passed to this handlers :attr:`callback`.

        Args:
            event (:obj:`dict`): Incoming Messenger JSON dict.

        Returns:
            :obj:`bool`
        """
        message = event.get('message')

        if not message:
            return False

        text = message.get('text')

        if text is not None:
            if self.pattern is not None:
                match = re.match(self.pattern, text)
                self.local.match = match
                return bool(match)
            else:
                return True
        return False

    def handle_event(self, event):
        """
        Send the event to the :attr:`callback`.

        Args:
            event (:obj:`dict`): Incoming Messenger event.
        """
        text = event['message'].get('text')

        kwargs = dict()
        kwargs['text'] = text

        if self.pattern is not None:
            match = self.local.match
            kwargs['groups'] = match.groups()
            kwargs['groupdict'] = match.groupdict()

        return self.callback(event, **kwargs)
