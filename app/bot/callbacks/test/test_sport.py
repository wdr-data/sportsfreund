from random import random

from lib.testing import ExpectedReply, event
from ..sport import api_discipline


def test_api_discipline(event):
    discipline = str(random())

    api_discipline(event, {'discipline': discipline})
    ExpectedReply(event).expect_text(f'Infos zum {discipline}')
