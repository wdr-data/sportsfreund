from ..fb import send_text, quick_reply
from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta

from time import sleep
import logging
logger = logging.Logger(__name__)

match = Match()


def api_next(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')

    # get_match_id_by_parameter
    if not discipline and not sport:
        send_text(sender_id,
                  'Interessiert dich Biathlon oder Ski Alpin?')
        return

    match_meta = MatchMeta.search_next(discipline=discipline or None, sport=sport or None)

    pl_next(event,{'calender.next': match_meta})



def pl_next(event, payload, **kwargs):
    sender_id = event['sender']['id']
    match_meta = payload['calender.next']

    # get_match_by_match_id


    send_text(sender_id, 'Moment, Ich schau kurz in meinem Kalender...')
    sleep(5)
    send_text(sender_id,
              'Ah! Hier steht es ja:\n {discipline} der {gender} in {town} am {date} um {time}'.format(
                  discipline = match_meta.discipline,
                  gender = match_meta.gender,
                  town = match_meta.town,
                  date = match_meta.match_date,
                  time = match_meta.match_time
              ),
              quick_replies=[
                  quick_reply('Ergebnis Dienst',
                              ['subscribe']
                              ),
                  quick_reply('Und das nächste?',
                              {'calender.next': match_meta}
                              )
              ])



def api_date(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    date = parameters.get('date')
    sport = parameters.get('sport')

    if not sport and not date:
        send_text('')