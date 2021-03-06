from unittest.mock import patch

from pytest import fixture
from collections import deque
from inspect import signature, Parameter

from lib.response import Replyable, SenderTypes


@fixture
def event():

    with patch('lib.response.Replyable') as Event:
        yield Event({}, type=SenderTypes.TEST)


class ExpectedReply:

    def __init__(self, replyable):
        self.replyable = replyable
        self.calls = deque(replyable.mock_calls)

    def expect_text(self, text, quick_replies=None):

        name, args, kwargs = self._get_next_call()

        texts = text if isinstance(text, list) else [text]
        quick_replieses = (
            quick_replies
            if quick_replies and isinstance(quick_replies[0], list)
            else [quick_replies]
        )

        assert name == 'send_text'
        assert kwargs['text'] in texts
        assert kwargs.get('quick_replies') in quick_replieses

        return self

    def expect_buttons(self, text, buttons):

        name, args, kwargs = self._get_next_call()

        texts = text if isinstance(text, list) else [text]
        buttonses = buttons if buttons and isinstance(buttons[0], list) else [buttons]

        assert name == 'send_text'
        assert kwargs['text'] in texts
        assert kwargs['buttons'] in buttonses

        return self

    def _get_next_call(self):
        actual = self.calls.popleft()
        name, args, kwargs = actual

        the_callable = getattr(Replyable({}, SenderTypes.TEST), name)

        positional_params = [
            arg_name for arg_name, arg in signature(the_callable).parameters.items()
            if arg.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.POSITIONAL_ONLY)
        ]

        for arg_name, arg_val in zip(positional_params, args):
            kwargs[arg_name] = arg_val

        return name, args, kwargs
