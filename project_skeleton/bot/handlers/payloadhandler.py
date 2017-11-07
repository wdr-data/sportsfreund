
import threading
import json

from .handler import Handler


class PayloadHandler(Handler):
    """
    Handler class to handle payloads from quick replies & buttons.

    Attributes:
        callback (:obj:`callable`): The callback function for this handler.
        keys (:obj:`list[str]`): A list of JSON keys that must be present in the payload

    Args:
        callback (:obj:`callable`): A function that takes ``event, **kwargs`` as arguments.
            It will be called when the :attr:`check_event` has determined that an event should be
            processed by this handler.
        keys (:obj:`list[str]`): A list of JSON keys that must be present in the payload

    """

    def __init__(self, callback, keys=None):
        super().__init__(callback)

        self.keys = keys

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
        postback = event.get('postback')
        payload = None

        if message and message.get('quick_reply'):
            payload = json.loads(message['quick_reply']['payload'])

        elif postback:
            payload = json.loads(postback['payload'])

        if payload is not None:
            self.local.payload = payload
            # Check if the payload JSON has all the keys we are looking for
            return all(key in payload for key in self.keys)

        else:
            return False

    def handle_event(self, event):
        """
        Send the event to the :attr:`callback`.

        Args:
            event (:obj:`dict`): Incoming Facebook event.
        """

        kwargs = dict()
        kwargs['payload'] = self.local.payload

        return self.callback(event, **kwargs)
