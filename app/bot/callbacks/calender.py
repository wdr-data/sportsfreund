from ..fb import send_text, quick_reply
from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta

from time import sleep
from datetime import datetime
import logging
logger = logging.Logger(__name__)

match = Match()


def api_next(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    town = parameters.get('town')
    # get_match_id_by_parameter
    if not discipline and not sport:
        send_text(sender_id,
                  'Interessiert dich Biathlon oder Ski Alpin?')
        return

    match_meta = MatchMeta.search_next(discipline=discipline or None, sport=sport or None)

    if not match_meta:
        if sport and discipline:
            send_text(sender_id, 'Ähm, sicher, dass es einen {sport} {discipline} gibt? Ich glaub nicht!'.format(
                sport = sport,
                discipline = discipline
            )
                      )
            return
        else:
            send_text(sender_id,
                      'Sorry, aber ich hab nix zu deiner Anfrage keinen konkreten Wettkampf in meinem Kalender gefunden.')
            return

    pl_next(event,{'calender.next': match_meta})



def pl_next(event, payload, **kwargs):
    sender_id = event['sender']['id']
    match_meta = payload['calender.next']

    # get_match_by_match_id


    send_text(sender_id, 'Moment, Ich schau kurz in meinen Kalender...')
    sleep(3)
    send_text(sender_id,
              'Ah! Hier hab ich es ja:')
    send_text(sender_id,
              '{date} um {time} Uhr, {discipline} {gender} in {town}'.format(
                  discipline = match_meta.discipline,
                  gender = 'der Damen ' if match_meta.gender == 'female' else( 'der Herren' if match_meta.gender == 'male'  else ''),
                  town = match_meta.town,
                  date = datetime.strptime(match_meta.match_date, '%Y-%m-%d').strftime('%d.%m.'),
                  time = match_meta.match_time
              ),
              quick_replies=[
                  quick_reply('Ergebnis Dienst',
                              ['subscribe']
                              )
              ]
              )



def api_date(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    date = parameters.get('date')
    sport = parameters.get('sport')

    if not sport and not date:
        send_text('')