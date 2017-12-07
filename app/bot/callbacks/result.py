import logging
from datetime import date as dtdate
from datetime import datetime

from ..handlers.payloadhandler import PayloadHandler
from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from feeds.models.team import Team
from lib.flag import flag
from lib.response import send_text, send_list, button_postback, send_buttons

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
                button=button_postback('Mehr Platzierungen', {'result_details': match.id})
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
                                     {'result_by_country': 'de', 'match_id': match_id}),
                     button_postback('Top 10', {'result_top_10': match_id}),
                     button_postback('Anderes Land',
                                     {'result_by_country': None, 'match_id': match_id})
                 ])


def result_top_10(event,payload):
    sender_id = event['sender']['id']
    match_id = payload['result_top_10']

    send_text(sender_id,
              f'Hier die Top 10 zur match_id {match_id}')


def result_by_country(event, payload):
    sender_id = event['sender']['id']
    country = payload['result_by_country']

    if not country:
        send_text(sender_id,
                  'Von welchem Land darf ich dir die platzierten Athleten zeigen?')
        # dummy to api
        return

    send_text(sender_id,
              f'Hier die Athleten aus Country {country}')


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
    PayloadHandler(result_top_10, ['result_top_10'])
]
