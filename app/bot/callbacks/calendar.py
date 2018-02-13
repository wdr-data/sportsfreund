import logging
from datetime import datetime, date, timedelta
from calendar import day_name
from time import sleep
import random

from ..handlers.payloadhandler import PayloadHandler
from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from feeds.config import supported_sports, sport_by_name, discipline_config
from lib.flag import flag
from lib.time import localtime_format
from lib.response import button_postback, quick_reply
from .result import api_podium

logger = logging.Logger(__name__)

match = Match()


def btn_event_today(event, payload):
    date = payload.get('event_today')
    api_next(event, parameters={'date': date})


def api_next(event, parameters, **kwargs):
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    town = parameters.get('town')
    p_date = parameters.get('date')
    period = parameters.get('date-period')
    country = parameters.get('country')
    gender = parameters.get('gender')
    round_mode = parameters.get('round_mode')

    if period:
        from_date, until_date = period_to_dates(period)

        if (until_date - from_date) <= timedelta(3) and until_date.weekday() > 4:
            event.send_text('An dem Wochenende hab ich folgende Termine:')
        elif until_date - from_date > timedelta(3):
            from_date = until_date - timedelta(3)
            event.send_text("Ich schau was ich im Zeitraum "
                            f"{date.strftime(from_date, '%d.%m.')}-"
                            f"{date.strftime(until_date, '%d.%m.%Y')} für dich an Events habe.")

        match_meta = MatchMeta.search_range(
            from_date=from_date, until_date=until_date, discipline=discipline, sport=sport,
            town=town, country=country, gender=gender, round_mode=round_mode)

        if not match_meta:
            match_meta = MatchMeta.search_range(
                from_date=from_date, until_date=until_date, gender=gender, round_mode=round_mode)

            if match_meta and (discipline or sport or town or country):
                event.send_text('Zu deiner Anfrage hab da leider keine Antwort, '
                                'aber vielleicht interessiert dich ja folgendes:')
                multiple_entry(event, match_meta)
            else:
                event.send_text(f"In dem Zeitraum "
                                f"{date.strftime(from_date, '%d.%m.')}-{date.strftime(until_date, '%d.%m.%Y')} "
                                f"ist mein Kalender leer.")
        else:
            multiple_entry(event, match_meta)
        return

    if p_date:
        d_date = datetime.strptime(p_date, '%Y-%m-%d').date()
        if d_date < date.today():
            api_podium(event, parameters, **kwargs)
        else:
            if round_mode == 'Finale' or round_mode == 'Entscheidung':
                match_meta = MatchMeta.search_date(date=d_date, discipline=discipline,
                                                   sport=sport, town=town, country=country,
                                                   gender=gender, round_mode=round_mode,
                                                   medals='all')
            else:
                match_meta = MatchMeta.search_date(date=d_date, discipline=discipline,
                                                   sport=sport, town=town, country=country,
                                                   gender=gender, round_mode=round_mode)

            if not match_meta:
                tomorrow = datetime.strptime(p_date, '%Y-%m-%d') + timedelta(days=1)
                match_meta = MatchMeta.search_date(date=tomorrow.date(),
                                                   sport=sport, town=town, country=country,
                                                   gender=gender, round_mode=round_mode)

            if not match_meta:
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
                if sport:
                    event.send_text(f'Eine Übersicht der nächsten Events im {sport}:')
                else:
                    event.send_text('Ein Übersicht der nächsten Events.')
                multiple_entry(event, match_meta)

        return

    if round_mode:
        today = date.today()

        if round_mode == 'Finale' or round_mode == 'Entscheidung':
            match_meta = MatchMeta.search_range(until_date=today, discipline=discipline,
                                                sport=sport, town=town, country=country,
                                                gender=gender,
                                                medals='all'
                                                )
        else:
            match_meta = MatchMeta.search_range(until_date=today, discipline=discipline,
                                                sport=sport, town=town, country=country,
                                                gender=gender, round_mode=round_mode,
                                                )

        if not match_meta and round_mode:
            event.send_text('Deine Anfrage führt bei mir leider ins Leere. Sry! 😪')
        else:
            event.send_text('In dieser Saison findet kein Weltcup mehr in '
                            f'{town if town else country} statt. Dafür hab ich hier bald die '
                            f'Ergebnisse aus {town if town else country}.')
    if country or town:
        match_meta = MatchMeta.search_range(until_date=today, discipline=discipline,
                                            sport=sport, town=town, country=country,
                                            gender=gender, round_mode=round_mode,
                                            )
        if not match_meta:
            event.send_text('Leider kein Event in {place}.'.format(place=town if town else country))
        else:
            if not round_mode:
                event.send_text('Folgende Events finden in {place} statt'.format(place=town if town else country))
            else:
                event.send_text(f'Folgende Events hab ich für dich:')
            multiple_entry(event, match_meta)
        return

    if not discipline and not sport:
        event.send_text('Mein Kalender ist voll mit Terminen. Was interessiert dich?\n'
                        'Termine für morgen? Nächstes Curling Spiel? Entscheidungen im Snowboard?'
                        ' Halbfinale im Eishockey der Damen?')
        return

    match_meta = MatchMeta.search_next(discipline=discipline, sport=sport,
                                           gender=gender, town=town, country=country,
                                           round_mode=round_mode)
    if not match_meta:
        match_meta = MatchMeta.search_next(discipline=discipline, sport=sport,
                                           gender=gender, round_mode=round_mode)

    if not match_meta:
        if sport and discipline:
            # follow up, because we have a yes/no question
            event.send_text(f'Ähm, sicher, dass es "{sport} - {discipline}" gibt?')

            return

        else:
            event.send_text('Sorry, aber ich hab zu deiner Anfrage keinen '
                            'konkreten Wettkampf in meinem Kalender gefunden.')
            return

    else:
        event.send_text('Moment, Ich schau kurz in meinen Kalender...')
        sleep(3)
        event.send_text(f'Ah! Hier hab ich ja das nächste '
                        f'{sport_by_name[match_meta.sport].competition_term}:')
        pl_entry_by_matchmeta(event, {'calendar.entry_by_matchmeta': match_meta,
                                      'add_options': True})


def multiple_entry(event, metas):

    overview = {}
    for name in sport_by_name:
        same_sport = [m for m in metas if m.sport == name]
        if same_sport:
            overview[name] = same_sport

    if len(overview) == 1:
        for k, v in overview.items():
            if len(v) == 1:
                for i in v:
                    pl_entry_by_matchmeta(event,
                                          {'calendar.entry_by_matchmeta': i,
                                           'one_in_many': False})
            else:
                send_more_cal_events_by_ids(event,
                                            {'send_more_cal_events_by_ids': [m.id for m in v],
                                             'sports_to_show': [k]})

        return
    else:
        medal_metas = [m for m in metas if m.medals]
        event.send_text(f'Hier die Medaillen Entscheidungen:')
        send_more_cal_events_by_ids(event,
                                    {'send_more_cal_events_by_ids': [m.id for m in medal_metas],
                                     'sports_to_show': [m.sport for m in medal_metas]}
                                    )
        quickies = []
        for sport, meta_list in overview.items():
            if len(meta_list) > 1:
                quickies.append(
                    quick_reply(f'{sport} ({len(meta_list)})',
                                 {'send_more_cal_events_by_ids': [m.id for m in metas],
                                  'sports_to_show': sport,
                                  'options': 'continue'}
                    )
                )
        if quickies:
            event.send_text(f'Insgesamt habe ich {len(metas)} Events für dich:',
                            quick_replies=quickies)


def send_more_cal_events_by_ids(event, payload, **kwargs):
    match_ids = payload['send_more_cal_events_by_ids']
    options = payload.get('options')
    sports_to_show = payload.get('sports_to_show')

    if not isinstance(sports_to_show, list):
        sports_to_show = [sports_to_show]

    all_metas = [MatchMeta.by_match_id(m_id) for m_id in match_ids]
    metas = [m for m in all_metas if m.sport in sports_to_show]

    if not metas:
        event.send_text('Keine weiteren Events gefunden 🔍')
        return

    start_date = metas[0].match_date
    event.send_text(f'Events am {metas[0].datetime.strftime("%d.%m.%Y")}:')
    for i, meta in enumerate(metas):
        if start_date != meta.match_date:
            start_date = meta.match_date
            event.send_text(f'Events am {meta.datetime.strftime("%d.%m.%Y")}:')

        pl_entry_by_matchmeta(event,
                              {'calendar.entry_by_matchmeta': meta,
                               'one_in_many': True})

        if i == len(metas)-1 and options == 'continue':
            quickies = []
            for sport in sport_by_name:
                meta_list = [m for m in all_metas if m.sport == sport]
                if meta_list and len(meta_list) > 1:
                    quickies.append(
                        quick_reply(f'{sport} ({len(meta_list)})',
                                    {'send_more_cal_events_by_ids': [m.id for m in meta_list],
                                     'sports_to_show': sport
                                     }
                                    )
                    )
            if quickies:
                event.send_text('Noch mehr?',
                                quick_replies=quickies
                                )



def pl_entry_by_matchmeta(event, payload, **kwargs):
    match_meta = payload['calendar.entry_by_matchmeta']
    one_in_many = payload.get('one_in_many', False)

    if not isinstance(match_meta, MatchMeta):
        match_meta = MatchMeta.by_id(match_meta)

    gender = ' der Damen' if match_meta.gender == 'female' \
        else (' der Herren' if match_meta.gender == 'male'  else '')

    is_olympia = match_meta.get('event') == MatchMeta.Event.OLYMPIA_18
    if 'medals' in match_meta:
        if match_meta.medals == 'complete':
            medals = f'{Match.medal(1)}{Match.medal(2)}{Match.medal(3)}'
        elif match_meta.medals == 'gold_silver':
            medals = f'{Match.medal(1)}{Match.medal(2)}'
        elif match_meta.medals == 'bronze_winner':
            medals = f'{Match.medal(3)}'
        else:
            medals = ''
    else:
        medals = ''

    if match_meta.match_incident:
        event.send_text(f"Ich habe gehört, der Wettkampf {match_meta.discipline} {gender}"
                        f" in {match_meta.town}, welcher am "
                        f"{day_name[match_meta.datetime.weekday()]}, {match_meta.datetime.strftime('%d.%m.%Y')} "
                        f"geplant war, sei {match_meta.match_incident.name}.")
    else:
        if not one_in_many:
            reply = f"Am {day_name[match_meta.datetime.weekday()]}, {match_meta.datetime.strftime('%d.%m.%Y')} " \
                    f"um {localtime_format(match_meta.datetime, event, is_olympia)}: "
        else:
            reply = f'{localtime_format(match_meta.datetime, event, is_olympia)} - '

        reply += f"{medals}{match_meta.sport}, "

        """
        type = discipline_config(match_meta.sport, match_meta.discipline_short).competition_type
        if type == 'ROBIN' or type == 'TOURNAMENT':
                home = match_meta.home
                away = match_meta.away
                reply += f"{match_meta.discipline_short}{gender}"
                reply += f'\n{home.name}{flag(home.country.iso)}:' \
                         f'{flag(away.country.iso)}{away.name}'
        else: \
        """
        reply += f"{match_meta.discipline_short}{gender} in {match_meta.town}"

        if match_meta.get('event') != MatchMeta.Event.OLYMPIA_18:
            reply += f" {flag(match_meta.venue.country.iso)} {match_meta.venue.country.code}"

        reply += '.'
        event.send_text(reply)


def period_to_dates(period):
    from_date = period.split('/')[0]
    from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    until_date = period.split('/')[1]
    until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
    return from_date, until_date

handlers = [
    PayloadHandler(send_more_cal_events_by_ids, ['send_more_cal_events_by_ids', 'sports_to_show']),
    PayloadHandler(btn_event_today, ['event_today']),
    ]
