from random import random
from unittest.mock import MagicMock

from lib.response import Replyable, SenderTypes
from ..general import api_discipline


def test_api_discipline():
    event = Replyable({}, type=SenderTypes.TEST)
    event.send_text = MagicMock()

    discipline = str(random())

    api_discipline(event, {'discipline': discipline})
    event.send_text.assert_called_with(f'Infos zum {discipline}')
