

class Handler(object):
    """
    The base class for all event handlers. You can create your own handlers by inheriting from
    this class.

    Attributes:
        callback (:obj:`callable`): The callback function for this handler.

    Args:
        callback (:obj:`callable`): A function that takes ``event, **kwargs`` as arguments.
            It will be called when the :attr:`check_event` has determined that an event should be
            processed by this handler.
    """

    def __init__(self, callback):
        self.callback = callback

    def check_event(self, event):
        """
        This method is called to determine if an event should be handled by
        this handler instance. It should always be overridden.

        Args:
            event (:obj:`dict`): The event to be tested.

        Returns:
            :obj:`bool`
        """
        raise NotImplementedError

    def handle_event(self, event):
        """
        This method is called if it was determined that an event should indeed
        be handled by this instance.

        Args:
            event (:obj:`dict`): The event to be handled.

        """
        raise NotImplementedError
