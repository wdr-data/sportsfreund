import logging
from datetime import datetime, date, timedelta
from time import sleep
from pycountry import countries

from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from lib.response import send_text
from lib.flag import flag

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
        from_date, until_date = period_to_dates(period)

        if (until_date - from_date) <= timedelta(3) and until_date.weekday() > 4:
            send_text(sender_id,
                      'An dem Wochenende hab ich folgende Termine:')
        elif until_date - from_date > timedelta(3):
            from_date = until_date - timedelta(3)
            send_text(
                sender_id,
                "Ich schau was ich im Zeitraum "
                f"{date.strftime(until_date - timedelta(3), '%d.%m.')}-"
                f"{date.strftime(until_date, '%d.%m.%Y')} für dich an Events habe.")

        match_meta = MatchMeta.search_range(
            from_date=from_date, until_date=until_date, discipline=discipline, sport=sport,
            town=town, country=country)

        if not match_meta:
            if discipline or sport or town or country:
                match_meta = MatchMeta.search_range(
                    from_date=from_date, until_date=until_date)
                if match_meta:
                    send_text(sender_id,
                              'Zu deiner Anfrage hab da leider keine Antwort, '
                              'aber vielleicht interessiert dich ja folgendes:')
                    multiple_entry(event, match_meta)
                else:
                    send_text(sender_id,
                              'In dem Zeitraum {from_da}-{till} ist mein Kalender leer.')
        else:
            multiple_entry(event, match_meta)
        return

    if p_date:
        d_date = datetime.strptime(p_date, '%Y-%m-%d').date()
        if d_date < date.today():
            send_text(
                sender_id,
                "Du informierst dich gerade darüber was in der Vergangenheit passieren wird. "
                f"Frag mich nochmal nach den Ergebnissen vom {date.strftime(d_date, '%d.%m.%Y')}.")
        else:
            send_text(sender_id,
                      'Gucken wir mal was da so los sein wird.')
            match_meta = MatchMeta.search_date(date=d_date, discipline=discipline,
                                               sport=sport, town=town, country=country)
            if not match_meta:
                if discipline or sport or town or country:
                    match_meta = MatchMeta.search_date(date=d_date)
                    if match_meta:
                        send_text(sender_id,
                                  'Zu deiner Anfrage hab da leider keine Antwort, '
                                  'aber vielleicht interessiert dich ja folgendes Event:')

                else:
                    send_text(sender_id,
                              'Kein Biathlon und auch kein Ski Alpin. '
                              'Zeit also um einen ☃ zu bauen!')
                    return
            multiple_entry(event, match_meta)

        return

    if town or country:
        today = date.today()
        match_meta = MatchMeta.search_range(from_date=today, discipline=discipline,
                                            sport=sport, town=town, country=country)
        if not match_meta:
            match_meta = MatchMeta.search_range(until_date=today, discipline=discipline,
                                                sport=sport, town=town, country=country)
            if not match_meta:
                send_text(sender_id,
                          'Leider kein Event in {place}.'.format(
                              place=town if town else country
                          ))
            else:
                send_text(sender_id,
                          'In dieser Sauson findet kein Weltcup mehr in '
                          f'{town if town else country} statt. Dafür hab ich hier bald die '
                          f'Ergebnisse aus {town if town else country}.')

        else:
            send_text(sender_id,
                      'Folgende Events finden in {place} statt'.format(
                          place=town if town else country
                      ))
            multiple_entry(event, match_meta)
        return

    if not discipline and not sport:
        send_text(sender_id,
                  'Suchst du nach einem Rennen im Biathlon oder Ski Alpin?')
        return

    # get_match_id_by_parameter
    match_meta = MatchMeta.search_next(discipline=discipline or None, sport=sport or None)

    if not match_meta:
        if sport and discipline:
            # follow up, because we have a yes/no question
            send_text(sender_id, f'Ähm, sicher, dass es "{sport} - {discipline}" gibt?')

            return

        else:
            send_text(sender_id,
                      'Sorry, aber ich hab nix zu deiner Anfrage keinen '
                      'konkreten Wettkampf in meinem Kalender gefunden.')
            return

    else:
        send_text(sender_id,
                  'Moment, Ich schau kurz in meinen Kalender...')
        sleep(3)
        send_text(sender_id,
                  f'Ah! Hier hab ich ja das nächste {match_meta.sport} Rennen:')
        pl_entry_by_matchmeta(event, {'calendar.entry_by_matchmeta': match_meta})


def multiple_entry(event, meta):
    sender_id = event['sender']['id']

    for match_meta in meta:
        pl_entry_by_matchmeta(event, {'calendar.entry_by_matchmeta': match_meta})


def pl_entry_by_matchmeta(event, payload, **kwargs):
    sender_id = event['sender']['id']
    match_meta = payload['calendar.entry_by_matchmeta']

    if not isinstance(match_meta, MatchMeta):
        match_meta = MatchMeta.by_id(match_meta)

    d_date = datetime.strptime(match_meta.match_date, '%Y-%m-%d')

    gender = 'der Damen ' if match_meta.gender == 'female' \
        else ('der Herren' if match_meta.gender == 'male'  else '')

    country = countries.get(alpha_3=match_meta.venue.country.code)

    send_text(sender_id,
              f"Am {int_to_weekday(d_date.weekday())}, {d_date.strftime('%d.%m.%Y')} um {match_meta.match_time} Uhr:"
              f"{match_meta.discipline} {gender}"
              f"in {match_meta.town} {flag(country.alpha_2)} {match_meta.venue.country.code}")


def period_to_dates(period):
    from_date = period.split('/')[0]
    from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    until_date = period.split('/')[1]
    until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
    return from_date, until_date


def int_to_weekday(int):
    day = {
        0: 'Montag',
        1: 'Dienstag',
        2: 'Mittwoch',
        3: 'Donnerstag',
        4: 'Freitag',
        5: 'Samstag',
        6: 'Sonntag',
        11: 'Wochenende',
        21: 'Woche'
    }
    return day[int]