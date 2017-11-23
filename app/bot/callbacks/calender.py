from ..fb import send_text
from feeds.models.match import Match

import logging
logger = logging.Logger(__name__)

match = Match()


def api_next(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')

    send_text(sender_id, 'Hier gibt es bald den das nächste Event')


