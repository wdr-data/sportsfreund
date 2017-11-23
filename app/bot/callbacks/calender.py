from ..fb import send_text, quick_reply
from feeds.models.match import Match

from time import sleep
import logging
logger = logging.Logger(__name__)

match = Match()


def api_next(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')

    # get_match_id_by_parameter
    match_id = 1234556
    pl_next(event,{'calender.next': match_id})



def pl_next(event, payload, **kwargs):
    sender_id = event['sender']['id']
    match_id = payload['calender.next']

    # get_match_by_match_id

    send_text(sender_id, 'Moment, Ich schau mal kurz in meinem Kalender...')
    sleep(5)
    send_text(sender_id,
              'Ah! Hier steht es ja:\n disziplin der gender in ort am Tag, datum um Uhrzeit',
              quick_replies=[
                  quick_reply('Ergebnis Dienst',
                              ['subscribe']),
                  quick_reply('Und das nächste?', ['calender.next'])
              ])

