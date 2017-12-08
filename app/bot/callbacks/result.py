import logging
from datetime import date as dtdate
from datetime import datetime

from lib.model import Model
from ..handlers.payloadhandler import PayloadHandler
from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from feeds.models.team import Team
from lib.flag import flag
from lib.response import send_text, send_list, button_postback, send_buttons, quick_reply

logger = logging.Logger(__name__)


def api_winner(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    date = parameters.get('date')
    period = parameters.get('date-period')
    town = parameters.get('town')
    country = parameters.get('country')

    if not discipline and not sport:
        send_text(sender_id,
                  'Meinst du im Biathlon oder Ski Alpin?')
        return

    if date and not period:
        date = datetime.strptime(date, '%Y-%m-%d').date()
        match_meta = MatchMeta.search_date(date=date, discipline=discipline,
                                           sport=sport, town=town, country=country)
        match_ids = [match.id for match in match_meta]
    elif period and not date:
        from_date = period.split('/')[0]
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        until_date = period.split('/')[1]
        until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
        match_meta = MatchMeta.search_range(
            from_date=from_date, until_date=until_date, discipline=discipline,sport=sport,
            town=town, country=country)
        match_ids = [match.id for match in match_meta]
    else:
        match_meta = [MatchMeta.search_last(discipline=discipline, sport=sport,
                                            town=town, country=country)]
        match_ids = [match.id for match in match_meta if match]
    asked_matches = [Match.by_id(id) for id in match_ids]

    if not asked_matches:
        send_text(sender_id,
                  'In dem angefragten Zeitraum haben keine Wettkämpfe stattgefunden.')
        return

    if not discipline:
        discipline = [match.discipline for match in match_meta]

    if not sport:
        sport = [match.sport for match in match_meta]

    if not isinstance(sport, list):
        sport = [sport] * len(asked_matches)

    if not isinstance(discipline, list):
        discipline = [discipline] * len(asked_matches)

    send_text(sender_id,
              'Folgende Wintersport-Ergebniss hab ich für dich:')
    for match, meta, sport, discipline in zip(asked_matches, match_meta, sport, discipline):
        if asked_matches[0].finished:
            results = match.match_result
            winner_team = Team.by_id(results[0].team_id)

            send_text(sender_id,
                      '{winner} hat {today} das {sport} Rennen in der Disziplin {discipline} '
                      'in {town}, {country} {date} gewonnen.'.format(
                          winner=' '.join([winner_team.name,
                                           flag(winner_team.country.iso),
                                           winner_team.country.code]),
                          sport=sport,
                          discipline=discipline,
                          town=meta.town,
                          country=meta.country,
                          date='am ' + meta.datetime.date().strftime('%d.%m.%Y')
                          if dtdate.today() != meta.datetime.date() else '',
                          today='heute' if dtdate.today() == meta.datetime.date() else ''

                      ))
        else:
            send_text(sender_id,
                      'Das Event {sport} {discipline} wurde noch nicht beendet. '
                      'Frage später erneut.'.format(
                          sport=sport,
                          discipline=discipline
                      ))


def api_podium(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    date = parameters.get('date')
    period = parameters.get('date-period')
    town = parameters.get('town')
    country = parameters.get('country')

    if date and not period:
        date = datetime.strptime(date, '%Y-%m-%d').date()
        match_meta = MatchMeta.search_date(
            date=date, discipline=discipline, sport=sport, town=town, country=country)
        match_ids = [match.id for match in match_meta]
    elif period and not date:
        from_date = period.split('/')[0]
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        until_date = period.split('/')[1]
        until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
        match_meta = MatchMeta.search_range(
            from_date=from_date, until_date=until_date, discipline=discipline,
            sport=sport, town=town, country=country)
        match_ids = [match.id for match in match_meta]
    else:
        match_meta = [MatchMeta.search_last(
            discipline=discipline, sport=sport, town=town, country=country)]
        match_ids = [match.id for match in match_meta if match]
    asked_matches = [Match.by_id(id) for id in match_ids]

    if not asked_matches:
        send_text(sender_id,
                  'In dem angefragten Zeitraum hat kein Wettkampf'
                  f'{(" in der Disziplin " + discipline) if discipline else ""} stattgefunden.')
        return

    if not discipline:
        discipline = [match.discipline for match in match_meta]

    if not sport:
        sport = [match.sport for match in match_meta]

    if not isinstance(sport, list):
        sport = [sport] * len(asked_matches)

    if not isinstance(discipline, list):
        discipline = [discipline] * len(asked_matches)

    if len(asked_matches)>1:
        send_text(sender_id, 'Folgende Wintersport-Ergebnisse hab ich für dich:')

    for match, meta, sport, discipline in zip(asked_matches, match_meta, sport, discipline):
        if match.finished:

            reply = 'Ergebnis beim {sport} {discipline} in {town}, {country}, am {day}, {date}:\n'\
                .format(
                    sport='⛷' if sport == 'Ski Alpin' else sport,
                    discipline=discipline,
                    town=meta.town,
                    country=flag(match.venue.country.iso),
                    day=int_to_weekday(meta.datetime.weekday()),
                    date=meta.datetime.date().strftime('%d.%m.%Y'),
                )

            send_text(sender_id, reply)

            send_list(
                sender_id,
                match.lst_podium,
                top_element_style='large',
                button=match.btn_podium
            )

        else:
            send_text(sender_id,
                      'Das Event {sport} {discipline} wurde noch nicht beendet. '
                      'Frage später erneut.'.format(
                          sport=sport,
                          discipline=discipline
                      ))


def result_details(event, payload):
    sender_id = event['sender']['id']
    match_id = payload['result_details']
    send_buttons(sender_id,
                 'Wovon denn?',
                 buttons=[
                     button_postback(f"{flag('DE')} Athleten",
                                     {'result_by_country': 'Deutschland', 'match_id': match_id}),
                     button_postback('Top 10', {'result_top_10': match_id}),
                     button_postback('Anderes Land',
                                     {'result_by_country': None, 'match_id': match_id})
                 ])


def result_total(event, payload):
    sender_id = event['sender']['id']
    step = payload['step']
    match_id = payload['result_total']
    match = Match.by_id(match_id)

    if step == 'top_10':
        results = match.results[:10]
        button = button_postback('Und der Rest?', {'result_total': match_id, 'step': None})
        result_kind = 'Top 10'
    else:
        results = match.results[11:]
        button = None
        result_kind = 'restlichen Ergebnisse'

    teams = [Team.by_id(result.team_id) for result in results]

    top_ten = '\n'.join(
        f'{r.rank}. {t.name} {flag(t.country.iso)} {match.txt_points(r)}'
        for r, t in zip(results, teams))

    if button:
        send_buttons(sender_id,
                     f'Hier die {result_kind} zu {match.meta.sport} {match.meta.discipline} '
                     f'in {match.meta.town}, {match.meta.country}: \n\n{top_ten}',
                     buttons=[button])
    else:
        send_text(sender_id,
                     f'Hier die {result_kind} zu {match.meta.sport} {match.meta.discipline} '
                     f'in {match.meta.town}, {match.meta.country}: \n\n{top_ten}')


def result_by_country(event, payload):
    sender_id = event['sender']['id']
    country_name = payload['result_by_country']
    match_id = payload['match_id']

    if not country_name:
        match = Match.by_id(match_id)
        countries = list({Team.by_id(result.team_id).country for result in match.results})[:10]

        quick = [quick_reply(f'{c.code} {flag(c.iso)}',
                             {'result_by_country' : c.name, 'match_id': match_id})
                 for c in countries]
        send_text(sender_id,
                  'Von welchem Land darf ich dir die platzierten Athleten zeigen?',
                  quick_replies=quick)
        return

    country = Model(Team.collection.find_one({'country': {'name': country_name}})['country'])
    match = Match.by_id(match_id)
    results = match.results_by_country(country.name)
    if not results:
        send_text(sender_id,
                  f'Es hat kein Athlet aus {country.code} {flag(country.iso)} das Rennen beendet.')
        return

    teams = [Team.by_id(result.team_id) for result in results]

    athletes_by_country = '\n'.join(
        f'{r.rank}. {t.name} {match.txt_points(r)}'
        for r, t in zip(results, teams))

    send_text(sender_id,
              f'Hier die Ergebnisse der Athleten aus {flag(country.iso)}in'
              f'in {match.meta.town}: \n\n{athletes_by_country}')


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


handlers = [
    PayloadHandler(result_details, ['result_details']),
    PayloadHandler(result_by_country, ['result_by_country', 'match_id']),
    PayloadHandler(result_total, ['result_total', 'step']),
]
