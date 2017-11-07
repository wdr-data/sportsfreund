
import logging
import threading

from .handler import Handler


class ConversationHandler(Handler):
    """
    A handler to hold a conversation with a single user

    The first collection, a ``list`` named :attr:`entry_points`, is used to initiate the
    conversation, for example with a :class:`PayloadHandler` or
    :class:`TextHandler`.

    The second collection, a ``dict`` named :attr:`states`, contains the different conversation
    steps and one or more associated handlers that should be used if the user sends a message when
    the conversation with them is currently in that state. You will probably use mostly
    :class:`TextHandler` and :class:`WitAiHandler` here.

    The third collection, a ``list`` named :attr:`fallbacks`, is used if the user is currently in a
    conversation but the state has either no associated handler or the handler that is associated
    to the state is inappropriate for the event, for example if the event contains a command, but
    a regular text message is expected. You could use this for a ``cancel`` command or to let the
    user know their message was not recognized.

    To change the state of conversation, the callback function of a handler must return the new
    state after responding to the user. If it does not return anything (returning ``None`` by
    default), the state will not change. To end the conversation, the callback function must
    return :attr`END` or ``-1``.

    Attributes:
        entry_points (List[:class:`Facebook.ext.Handler`]): A list of ``Handler`` objects that can
            trigger the start of the conversation.
        states (Dict[:obj:`object`, List[:class:`Facebook.ext.Handler`]]): A :obj:`dict` that
            defines the different states of conversation a user can be in and one or more
            associated ``Handler`` objects that should be used in that state.
        fallbacks (List[:class:`Facebook.ext.Handler`]): A list of handlers that might be used if
            the user is in a conversation, but every handler for their current state returned
            ``False`` on :attr:`check_event`.
        allow_reentry (:obj:`bool`): Optional. Determines if a user can restart a conversation with
            an entry point.

    Args:
        entry_points (List[:class:`Facebook.ext.Handler`]): A list of ``Handler`` objects that can
            trigger the start of the conversation. The first handler which :attr:`check_event`
            method returns ``True`` will be used. If all return ``False``, the event is not
            handled.
        states (Dict[:obj:`object`, List[:class:`Facebook.ext.Handler`]]): A :obj:`dict` that
            defines the different states of conversation a user can be in and one or more
            associated ``Handler`` objects that should be used in that state. The first handler
            which :attr:`check_event` method returns ``True`` will be used.
        fallbacks (List[:class:`Facebook.ext.Handler`]): A list of handlers that might be used if
            the user is in a conversation, but every handler for their current state returned
            ``False`` on :attr:`check_event`. The first handler which :attr:`check_event` method
            returns ``True`` will be used. If all return ``False``, the event is not handled.
        allow_reentry (:obj:`bool`, optional): If set to ``True``, a user that is currently in a
            conversation can restart the conversation by triggering one of the entry points.

    Raises:
        ValueError
    """

    END = -1
    """:obj:`int`: Used as a constant to return when a conversation is ended."""

    def __init__(self,
                 entry_points,
                 states,
                 fallbacks,
                 allow_reentry=False):

        self.entry_points = entry_points
        self.states = states
        self.fallbacks = fallbacks

        self.allow_reentry = allow_reentry

        self.conversations = dict()

        # We use this to carry data from check_event to handle_event in multi-threaded environments
        self.local = threading.local()

        self.logger = logging.getLogger(__name__)

    def check_event(self, event):
        """
        Determines whether an event should be handled by this conversationhandler, and if so in
        which state the conversation currently is.

        Args:
            event (:obj:`dict`): Incoming Facebook event.

        Returns:
            :obj:`bool`
        """

        key = event['sender']['id']
        state = self.conversations.get(key)

        self.logger.debug('Selecting conversation %s with state %s' % (str(key), str(state)))

        handler = None

        # Search entry points for a match
        if state is None or self.allow_reentry:
            for entry_point in self.entry_points:
                if entry_point.check_event(event):
                    handler = entry_point
                    break

            else:
                if state is None:
                    return False

        # Get the handler list for current state, if we didn't find one yet and we're still here
        if state is not None and not handler:
            handlers = self.states.get(state)

            for candidate in (handlers or []):
                if candidate.check_event(event):
                    handler = candidate
                    break

            # Find a fallback handler if all other handlers fail
            else:
                for fallback in self.fallbacks:
                    if fallback.check_event(event):
                        handler = fallback
                        break

                else:
                    return False

        # Save the current user and the selected handler for handle_event
        self.local.current_conversation = key
        self.local.current_handler = handler

        return True

    def handle_event(self, event):
        """
        Send the event to the callback for the current state and Handler

        Args:
            event (:obj:`dict`): Incoming Facebook event.
        """

        new_state = self.local.current_handler.handle_event(event)

        self.change_state(new_state, self.local.current_conversation)

    def change_state(self, new_state, key):
        if new_state == self.END:
            if key in self.conversations:
                del self.conversations[key]
            else:
                pass

        elif new_state is not None:
            self.conversations[key] = new_state
