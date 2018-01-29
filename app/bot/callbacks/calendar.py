import logging
from datetime import datetime, date, timedelta
from calendar import day_name
from time import sleep
import random

from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from feeds.config import supported_sports, sport_by_name
from lib.flag import flag
from .result import api_podium

logger = logging.Logger(__name__)

match = Match()


def api_next(event, parameters, **kwargs):
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    town = parameters.get('town')
    p_date = parameters.get('date')
    period = parameters.get('date-period')
    country = parameters.get('country')
    gender = parameters.get('gender')

    if period:
        from_date, until_date = period_to_dates(period)

        if (until_date - from_date) <= timedelta(3) and until_date.weekday() > 4:
            event.send_text('An dem Wochenende hab ich folgende Termine:')
        elif until_date - from_date > timedelta(3):
            from_date = until_date - timedelta(3)
            event.send_text("Ich schau was ich im Zeitraum "
                            f"{date.strftime(until_date - timedelta(3), '%d.%m.')}-"
                            f"{date.strftime(until_date, '%d.%m.%Y')} für dich an Events habe.")

        match_meta = MatchMeta.search_range(
            from_date=from_date, until_date=until_date, discipline=discipline, sport=sport,
            town=town, country=country, gender=gender)

        if not match_meta:
            match_meta = MatchMeta.search_range(
                from_date=from_date, until_date=until_date, gender=gender)

            if match_meta and (discipline or sport or town or country):
                event.send_text('Zu deiner Anfrage hab da leider keine Antwort, '
                                'aber vielleicht interessiert dich ja folgendes:')
                multiple_entry(event, match_meta)
            else:
                event.send_text('In dem Zeitraum {from_da}-{till} ist mein Kalender leer.')
        else:
            multiple_entry(event, match_meta)
        return

    if p_date:
        d_date = datetime.strptime(p_date, '%Y-%m-%d').date()
        if d_date < date.today():
            api_podium(event, parameters, **kwargs)
        else:
            event.send_text('Gucken wir mal was da so los sein wird.')
            match_meta = MatchMeta.search_date(date=d_date, discipline=discipline,
                                               sport=sport, town=town, country=country,
                                               gender=gender)
            if not match_meta:
                match_meta = MatchMeta.search_date(date=d_date, gender=gender)
                if match_meta and (discipline or sport or town or country):
                    event.send_text('Zu deiner Anfrage hab da leider keine Antwort, '
                                    'aber vielleicht interessiert dich ja folgendes Event:')
                    multiple_entry(event, match_meta)
                    return
                else:
                    emoji = ['⛷', '🏂']
                    event.send_text('Heute findet kein Wintersport-Event statt. '
                                    f'Ich geh ne Runde {random.choice(emoji)}!')
                    return
            else:
                multiple_entry(event, match_meta)

        return

    if town or country:
        today = date.today()
        match_meta = MatchMeta.search_range(from_date=today, discipline=discipline,
                                            sport=sport, town=town, country=country, gender=gender)
        if not match_meta:
            match_meta = MatchMeta.search_range(until_date=today, discipline=discipline,
                                                sport=sport, town=town, country=country,
                                                gender=gender)
            if not match_meta:
                event.send_text('Leider kein Event in {place}.'.format(place=town if town else country))
            else:
                event.send_text('In dieser Sauson findet kein Weltcup mehr in '
                                f'{town if town else country} statt. Dafür hab ich hier bald die '
                                f'Ergebnisse aus {town if town else country}.')

        else:
            event.send_text('Folgende Events finden in {place} statt'.format(place=town if town else country))
            multiple_entry(event, match_meta)
        return

    if not discipline and not sport:
        event.send_text('Mein Kalender ist voll mit Terminen. '
                        'Such dir eine der folgenden Sportarten aus:')
        sports_to_choose = ''
        for i, sport in enumerate(supported_sports):
            if i == len(supported_sports) - 1:
                sports_to_choose += f'oder {sport}.'
            else:
                sports_to_choose += f'{sport}, '
        event.send_text(sports_to_choose)
        return

    # get_match_id_by_parameter
    match_meta = MatchMeta.search_next(discipline=discipline, sport=sport,
                                       gender=gender)

    if not match_meta:
        if sport and discipline:
            # follow up, because we have a yes/no question
            event.send_text(f'Ähm, sicher, dass es "{sport} - {discipline}" gibt?')

            return

        else:
            event.send_text('Sorry, aber ich hab nix zu deiner Anfrage keinen '
                            'konkreten Wettkampf in meinem Kalender gefunden.')
            return

    else:
        event.send_text('Moment, Ich schau kurz in meinen Kalender...')
        sleep(3)
        event.send_text(f'Ah! Hier hab ich ja das nächste '
                        f'{sport_by_name[match_meta.sport].competition_term}:')
        pl_entry_by_matchmeta(event, {'calendar.entry_by_matchmeta': match_meta})


def multiple_entry(event, meta):
    start_date = datetime.strptime("1990-1-1", '%Y-%m-%d')

    for i, match_meta in enumerate(meta):
        match_date = datetime.strptime(match_meta.match_date, '%Y-%m-%d')
        if start_date != match_date:
            event.send_text(f"{day_name[match_date.weekday()]},"
                            f" {match_date.strftime('%d.%m.%Y')}")
            start_date = match_date
        if i == 11:
            event.send_text(f'Hier höre ich mal auf, denn in meinem Kalender sind noch {len(meta)-i} Events. '
                            f"Schränk' deine Suche doch ein wenig ein.")
            return

        pl_entry_by_matchmeta(event, {'calendar.entry_by_matchmeta': match_meta,
                                      'one_in_many': True})


def pl_entry_by_matchmeta(event, payload, **kwargs):
    match_meta = payload['calendar.entry_by_matchmeta']
    one_in_many = payload.get('one_in_many', False)

    if not isinstance(match_meta, MatchMeta):
        match_meta = MatchMeta.by_id(match_meta)

    d_date = datetime.strptime(match_meta.match_date, '%Y-%m-%d')

    gender = ' der Damen' if match_meta.gender == 'female' \
        else (' der Herren' if match_meta.gender == 'male'  else '')

    if match_meta.match_incident:
        event.send_text(f"Ich habe gehört, der Wettkampf {match_meta.discipline} {gender}"
                        f" in {match_meta.town}, "
                        f"welcher am {day_name[d_date.weekday()]}, {d_date.strftime('%d.%m.%Y')} "
                        f"geplant war, sei {match_meta.match_incident.name}.")
    else:
        if not one_in_many:
            reply = f"Am {day_name[d_date.weekday()]}, {d_date.strftime('%d.%m.%Y')} " \
                    f"um {match_meta.match_time} Uhr:"
        else:
            reply = f'{match_meta.match_time} Uhr - '

        event.send_text(reply+ f"{match_meta.sport}, "
                               f"{match_meta.discipline_short}{gender} in {match_meta.town} "
                               f"{flag(match_meta.venue.country.iso)} "
                               f"{match_meta.venue.country.code}")


def period_to_dates(period):
    from_date = period.split('/')[0]
    from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    until_date = period.split('/')[1]
    until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
    return from_date, until_date
