import logging
from datetime import date as dtdate
from datetime import datetime, timedelta
from calendar import day_name

from lib.model import Model
from lib.time import localtime_format
from ..handlers.payloadhandler import PayloadHandler
from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from feeds.config import discipline_config
from feeds.config import SUPPORTED_SPORTS, SPORT_BY_NAME
from lib.flag import flag
from lib.emoij_number import emoji_number
from lib.response import button_postback, quick_reply, list_element

logger = logging.Logger(__name__)


def api_winner(event, parameters, **kwargs):
    api_podium(event, parameters)


def btn_podium(event, payload):
    sport = payload.get('podium')
    api_podium(event, parameters={'sport': sport})


def api_podium(event, parameters, **kwargs):
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    date = parameters.get('date')
    period = parameters.get('date-period')
    town = parameters.get('town')
    country = parameters.get('country')
    gender = parameters.get('gender')
    round_mode = parameters.get('round_mode')

    if date:
        date = datetime.strptime(date, '%Y-%m-%d').date()
        if date > dtdate.today():
            date = date.replace(date.year - 1)
            if date.day == 29 and date.month == 2 and date.year % 4 != 0:
                event.send_text('Nice try, aber wir befinden und nicht in einem Schaltjahr. 😎')
                return

        match_metas = MatchMeta.search_date(
            date=date, discipline=discipline, sport=sport, town=town,
            country=country, gender=gender)
    elif period and not date:
        from_date = period.split('/')[0]
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        until_date = period.split('/')[1]
        until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
        match_metas = MatchMeta.search_range(
            from_date=from_date, until_date=until_date, discipline=discipline,
            sport=sport, town=town, country=country, gender=gender)
    elif town or country:
        match_metas = MatchMeta.search_range(
            until_date=dtdate.today(), discipline=discipline, sport=sport,
            town=town, country=country, gender=gender)
    elif round_mode:
        match_metas = MatchMeta.search_range(
            until_date=dtdate.today(), discipline=discipline, sport=sport,
            town=town, country=country, gender=gender, round_mode=round_mode)
        if not match_metas and round_mode == 'Finale':
            match_metas = MatchMeta.search_range(
                until_date=dtdate.today(), discipline=discipline, sport=sport,
                town=town, country=country, gender=gender, round_mode='Entscheidung')
            if not match_metas:
                match_metas = MatchMeta.search_range(
                    until_date=dtdate.today(), discipline=discipline, sport=sport,
                    town=town, country=country, gender=gender)
    else:

        match_metas = [MatchMeta.search_last(
            sport=sport, discipline=discipline, town=town, country=country, gender=gender)]
        reply = ''
        if match_metas[0] is None:
            reply += 'Hmm dazu habe ich noch keine Ergebnisse in meiner Datenbank 🤔'

        elif match_metas[0].event != MatchMeta.Event.OLYMPIA_18:
            reply += '🚨Aus PyeongChang 🇰🇷 liegen noch keine aktuellen Ergebnisse vor!🚨' \
                     'Aber hier ist das letzte {event_title}:'.format(
                event_title='Weltcup Ergebnis' if match_metas[0].event.value == 'worldcup' else
                'Ergebnis aus Sotschi'
            )
        else:
            reply += 'Hier das letzte Event in meiner Datenbank:'
        event.send_text(reply)

    match_ids = [match.id for match in match_metas if match]

    if not match_ids:
        event.send_text('In diesem Zeitraum hat kein Event stattgefunden.')
        return

    result_podium(event, {'result_podium': match_ids})


def result_podium(event, payload):
    # payload is list of match_ids
    match_ids = payload['result_podium']
    match_metas = []
    asked_matches = []

    for match_id in match_ids:
        # Skip deleted matches
        try:
            asked_matches.append(Match.by_id(match_id))
            match_metas.append(MatchMeta.by_match_id(match_id))

        except ValueError:
            pass

    discipline = [match.discipline for match in match_metas]

    sport = [match.sport for match in match_metas]

    if len(asked_matches)>1:
        event.send_text('Bitteschön:')

    counter = 0
    for  match, meta, sport, discipline in zip(asked_matches, match_metas, sport, discipline):
        counter += 1
        if counter > 8:
            event.send_text(f'So, ich hab hier noch {len(asked_matches)-8} Events in der Pipline '
                            f'die alle auf deine Suchanfrage passen.'
                            f' Schränk deine Suche bitte ein wenig ein!')
            return

        if match.match_incident:
            if match.match_incident.id == '3' or match.match_incident.id == '4':
                event.send_text(f'{match.match_incident.name}: '
                                f'{meta.discipline_short}, {meta.gender_name}'
                                f'in {meta.town}')
            else:
                send_result(event, match)
        elif match.finished:
            send_result(event, match)

        else:
            event.send_text(f'Das Event {sport} {meta.discipline_short} in '
                            f'{meta.town} wurde noch nicht beendet. '
                            f'Frag bitte später noch mal. Wenn Du mir "Für {sport} anmelden"'
                            f' schreibst, melde ich mich, wenn ich das Ergebnis habe'
                            )


def result_details(event, payload):
    match_id = payload['result_details']
    event.send_buttons('Was interessiert dich?',
         buttons=[
             button_postback(f"Deutsche Sportler",
                             {'result_by_country': 'Deutschland', 'match_id': match_id}),
             button_postback('Top 10', {'result_total': match_id, 'step': 'top_10'}),
             button_postback('Anderes Land',
                             {'result_by_country': None, 'match_id': match_id})
         ]
    )


def result_total(event, payload):
    step = payload['step']
    match_id = payload['result_total']

    try:
        match = Match.by_id(match_id)
    except ValueError:
        event.send_text('Dieses Event kann ich in meiner Datenbank nicht mehr finden :/')

    buttons = []
    if step == 'top_10' or step == 'round_mode':
        results = match.results[:10]
        if len(match.results) > 10:
            buttons.append(
                button_postback('Und der Rest?',
                                {'result_total': match_id, 'step': None}))
            buttons.append(
                button_postback(f"Deutsche Sportler",
                                {'result_by_country': 'Deutschland',
                                            'match_id': match_id}))
            buttons.append(
                button_postback('Anderes Land',
                                {'result_by_country': None, 'match_id': match_id}))

        result_kind = f'Top {len(results)}'
    else:
        results = match.results[10:]
        result_kind = 'restlichen Ergebnisse'

    teams = [result.team for result in results]

    if 'medals' in match.meta and match.meta.medals == 'complete':
        top_ten = '\n'.join(
            f'{match.medal(int(r.rank))}. {t.name} {flag(t.country.iso)}'
            f' {t.country.code} {match.txt_points(r)}'
            for r, t in zip(results, teams))
    else:
        top_ten = '\n'.join(
            f'{r.rank}. {t.name} {flag(t.country.iso)} {t.country.code} {match.txt_points(r)}'
            for r, t in zip(results, teams))

    config = discipline_config(match.meta.sport, match.meta.discipline_short)

    if isinstance(config, dict) and 'rounds' in config and config['rounds']:
        reply = f'{match.meta.sport}, ' \
                f'{match.meta.discipline_short}, {match.meta.gender_name}\n' \
                f'⚡{match.meta.round_mode}⚡'

        is_olympia = match.meta.get('event') == MatchMeta.Event.OLYMPIA_18

        if step == 'top_10':
            reply += f'\n{day_name[match.datetime.weekday()]}, {match.datetime.strftime("%d.%m.%Y")} ' \
                     f'um {localtime_format(match.datetime, event, is_olympia)} ' \
                     f'in {match.venue.town.name}'
        elif step == 'round_mode':
            reply += f'\n{day_name[match.datetime.weekday()]}, {match.datetime.strftime("%d.%m.%Y")} ' \
                     f'um {localtime_format(match.datetime, event, is_olympia)} ' \
                     f'in {match.venue.town.name}'
    else:
        reply = f'Hier die {result_kind} zu {match.meta.sport} {match.meta.discipline_short} ' \
                f'in {match.meta.town}, {match.meta.country}:'

    reply = f'{reply}\n\n{top_ten}'

    if buttons:
        event.send_buttons(reply, buttons=buttons)
    else:
        event.send_text(reply)


def result_by_country(event, payload):
    country_name = payload['result_by_country']
    match_id = payload['match_id']

    try:
        match = Match.by_id(match_id)
    except ValueError:
        event.send_text('Dieses Event kann ich in meiner Datenbank nicht mehr finden :/')

    if not country_name:
        countries_all = [result.team.country for result in match.results]
        countries = [ii for n, ii in enumerate(countries_all) if ii not in countries_all[:n]]

        quick = [quick_reply(f'{flag(c.iso)} {c.code}',
                             {'result_by_country' : c.name, 'match_id': match_id})
                 for c in countries[:11]]

        event.send_text('Welches Land möchtest du?',
                        quick_replies=quick)
        return

    results_all = match.results_by_country(country_name)
    results = []
    for r in results_all:
        results.append(r)

    if not results:
        event.send_text(f'Kein Athlet aus {country_name}'
                        f' hat das {SPORT_BY_NAME[match.meta.sport].competition_term} beendet.')
        return

    teams = [result.team for result in results]
    country = teams[0].country

    if 'medals' in match.meta and match.meta.medals == 'complete':
        athletes_by_country = '\n'.join(
            f'{match.medal(int(r.rank))}. {t.name} {match.txt_points(r)}'
            for r, t in zip(results, teams))
    else:
        athletes_by_country = '\n'.join(
            f'{r.rank}. {t.name} {match.txt_points(r)}'
            for r, t in zip(results, teams))

    event.send_text(f'Hier die Ergebnisse aus {flag(country.iso)} {country.code} '
                    f'in {match.meta.town}: \n\n{athletes_by_country}')


def send_result(event, match):

    if match.meta.sport == 'Eishockey' or match.meta.sport == 'Curling':
        result_game(event, match)
        return

    if 'medals' in match.meta and match.meta.medals or match.meta.event == MatchMeta.Event.WORLDCUP:
        if match.meta.event == MatchMeta.Event.WORLDCUP or match.meta.medals == 'complete':
            button = match.btn_podium
        else:
            button = None

        list = match.lst_podium

        if len(list) > 1:
            event.send_list(
                    list,
                    top_element_style='large',
                    button=button
            )
            return
        else:
            event.send_text('Tut mir Leid, dazu habe ich derzeit keine Informationen.')


    result_total(event, {'result_total': match.id, 'step': 'round_mode'})


def result_game(event, match):
    year = match.datetime.strftime("%Y")
    if match.meta.sport == 'Curling':
        reply_title = '🥌 '
    else:
        reply_title = ''
    reply_title += f'{match.meta.sport}, {match.meta.gender_name} ⚡{match.meta.round_mode}⚡'
    time = localtime_format(match.datetime, event, is_olympia=match.meta.get('event') == MatchMeta.Event.OLYMPIA_18)
    reply_sbtl = f'{day_name[match.datetime.weekday()]}, ' \
             f'{match.datetime.strftime("%d.%m.%Y")} um {time}\n'
    reply = reply_title + '\n' + reply_sbtl
    results = match.results
    home = results[0]
    away = results[1]
    if len(results) == 2:
        if match.meta.round_mode == 'Finale':
            home_medal = Match.medal(1) if home.match_result > \
                                             away.match_result else Match.medal(2)
            away_medal = Match.medal(2) if home.match_result > \
                                             away.match_result else Match.medal(1)
            first = f'Olympiasieger {year}'
            medal_first = Match.medal(1)
            second = f'Zweiter der Olympischen Spiele {year}'
            medal_second = Match.medal(2)
        elif match.meta.round_mode == '3. Platz':
            home_medal = Match.medal(3) if home.match_result > \
                                             away.match_result else f'{Match.medal(4)}.'
            away_medal = f'{Match.medal(4)}.' if home.match_result > \
                                             away.match_result else Match.medal(3)
            first = f'Dritter der Olympischen Spiele {year}'
            medal_first = Match.medal(3)
            second = f'Vierter der Olympischen Spiele {year}'
            medal_second = f'{Match.medal(4)}.'
        else:
            home_medal = ''
            away_medal = ''

        reply_game = f'{home.team.name} {flag(home.team.country.iso)} ' \
                     f' {emoji_number(home.match_result)}➖{emoji_number(away.match_result)}' \
                     f'  {flag(away.team.country.iso)} {away.team.name}'
        reply += f'{home_medal} {reply_game} {away_medal}'
        if match.match_incident:
            incident = f'++ Entscheidung fiel {match.match_incident.name} ++ '
            reply += f'\n{incident}'
        else:
            incident = f'{match.meta.round_mode}'

        if match.meta.round_mode != 'Finale' and match.meta.round_mode != '3. Platz':
            if match.meta.round_mode in ['Gruppe A', 'Gruppe B', 'Gruppe C', 'Round Robin']:
                event.send_buttons(reply,
                                   buttons=[
                                       button_postback(f'Tabelle {match.meta.round_mode}',
                                                       {'sport': match.meta.sport,
                                                        'season_id': match.meta.season_id,
                                                        'round_name': match.meta.round_mode,
                                                        'gender': match.meta.gender}
                                                       )
                                   ]

                )
            else:
                event.send_text(reply)

        else:
            winner = home if home.match_result > away.match_result else away
            loser = away if home == winner else home
            list_medal =[
                list_element(reply_title,
                             reply_sbtl,
                             image_url=SPORT_BY_NAME[match.meta.sport].picture_url
                ),
                list_element(f'{medal_first} {winner.team.name} {flag(winner.team.country.iso)}',
                             f'{first}'),
                list_element(f'{medal_second} {loser.team.name} {flag(loser.team.country.iso)}',
                             f'{second}'),
                list_element(f'{reply_game}',
                             f'{incident}')
            ]
            event.send_list(list_medal,
                            top_element_style='large'
                            )
    else:
        result_total(event, match)


def pl_send_result(event, payload):
    match_id = payload.get('match_id')

    match = Match.by_id(match_id)
    send_result(event, match)


handlers = [
    PayloadHandler(pl_send_result, ['match_id', 'result']),
    PayloadHandler(btn_podium, ['podium']),
    PayloadHandler(result_details, ['result_details']),
    PayloadHandler(result_by_country, ['result_by_country', 'match_id']),
    PayloadHandler(result_total, ['result_total', 'step']),
]
