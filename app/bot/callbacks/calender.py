from ..fb import send_text, quick_reply
from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta

from time import sleep
from datetime import datetime, date, timedelta

import logging
logger = logging.Logger(__name__)

match = Match()


def api_next(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    town = parameters.get('town')
    p_date = parameters.get('date')
    period = parameters.get('date-period')
    country = parameters.get('country')

    if period:
        from_date,until_date = period_to_dates(period)

        if (until_date - from_date) <= timedelta(3) and until_date.weekday() > 4:
            send_text(sender_id,
                      'An dem Wochenende hab ich folgende Termine:')
        elif until_date - from_date > timedelta(3):
            send_text(sender_id,
                      'Ich schau mir nur die Tage {from_da}-{till} an.'.format(
                till = date.strftime(until_date, '%d.%m.%Y'),
                from_da = date.strftime(until_date-timedelta(3), '%d.%m.')
            ))
            #match_meta = get_list_match_meta(period,parameters)
        match_meta = 1
        if match_meta == 1:
            send_text(sender_id,
                      'we have matches in this period')
        else:
            send_text(sender_id,
                      '')
        return

    if p_date:
        d_date = datetime.strptime(p_date, '%Y-%m-%d').date()
        if d_date < date.today():
            send_text(sender_id,
                      'Du informierst dich gerade darüber was in der Vergangenheit passieren wird. Ich zeig dir mal die Ergebnisse vom {date}.'.format(
                date=date.strftime(d_date,'%d.%m.%Y')
            )
            )
        else:
            send_text(sender_id,
                      'Gucken wir mal was da so los sein wird.')
            #match_meta = MatchMeta.search_date( date)
            match_meta = 0
            if match_meta:
                send_text(sender_id, 'there is an event held on that date {date}'.format(
                    date=date.strftime(d_date,'%d.%m.%Y')
                ))
            else:
                send_text(sender_id,
                          'On this day is no event you asked for'+p_date)

        return

    if town or country:
        match_meta = 1
        if match_meta:
            send_text(sender_id,
                      'Es gibt ein Rennen in ' + town)
        else:
            send_text(sender_id,
                      'Es gibt kein Rennen in '+ town)
        return



    if not discipline and not sport:
        send_text(sender_id,
                  'Suchst du nach einem Biathlon oder Ski Alpin rennen?')
        return

    # get_match_id_by_parameter
    match_meta = MatchMeta.search_next(discipline=discipline or None, sport=sport or None)

    if not match_meta:
        if sport and discipline:
            # follow up, because we have a yes/no question
            send_text(sender_id, 'Ähm, sicher, dass es {sport} - {discipline} gibt?'.format(
                sport = sport,
                discipline = discipline
            )
                      )

            return

        else:
            send_text(sender_id,
                      'Sorry, aber ich hab nix zu deiner Anfrage keinen konkreten Wettkampf in meinem Kalender gefunden.')
            return

    else:
        send_text(sender_id,
                  'Moment, Ich schau kurz in meinen Kalender...')
        sleep(3)
        send_text(sender_id,
                  'Ah! Hier hab ich es ja:')
        pl_entry_by_matchmeta(event,{'calender.entry_by_matchmeta': match_meta})



def pl_entry_by_matchmeta(event, payload, **kwargs):
    sender_id = event['sender']['id']
    match_meta = payload['calender.entry_by_matchmeta']
    d_date = datetime.strptime(match_meta.match_date, '%Y-%m-%d')

    # get_match_by_match_id
    send_text(sender_id,
              '{day}, {date}, um {time}Uhr, {discipline} {gender} in {town}'.format(
                  discipline=match_meta.discipline,
                 gender='der Damen ' if match_meta.gender == 'female' else( 'der Herren' if match_meta.gender == 'male'  else ''),
                  town=match_meta.town,
                  day= int_to_weekday(d_date.weekday()),
                  date=d_date.strftime('%d.%m.'),
                  time=match_meta.match_time
              ),
              quick_replies=[
                  quick_reply('Ergebnis Dienst',
                              ['subscribe']
                              )
              ]
              )




def period_to_dates(period):
    from_date = period.split('/')[0]
    from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    until_date = period.split('/')[1]
    until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
    return from_date,until_date

def int_to_weekday(int):
    day = {
        0 : 'Montag',
        1 : 'Dienstag',
        2 : 'Mittwoch',
        3 : 'Donnerstag',
        4 : 'Freitag',
        5 : 'Samstag',
        6 : 'Sonntag',
        11 : 'Wochenende',
        21: 'Woche'
    }
    return day[int]

def get_list_match_meta(kind,parameters):

    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    town = parameters.get('town')
    p_date = parameters.get('date')
    period = parameters.get('date-period')
    country = parameters.get('country')

    if kind == period:
        from_date,until_date = period_to_dates(period)

        match_meta =1
    elif kind == date:
        match_meta =0

    elif kind == town:
        match_meta =0

    elif kind == country:
        match_meta = 0

    elif kind == discipline:
        match_meta = 0

    elif kind == sport:
        match_meta = 0

    else:
        match_meta = []

    return match_meta


