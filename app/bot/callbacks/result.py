import logging
from datetime import date as dtdate
from datetime import datetime

from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from feeds.models.team import Team
from lib.response import send_text

logger = logging.Logger(__name__)

OFFSET = 127462 - ord('A')


def flag(code):
    return chr(ord(code[0]) + OFFSET) + chr(ord(code[1]) + OFFSET)


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
        match_id = [match.id for match in match_meta]
    elif period and not date:
        from_date = period.split('/')[0]
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        until_date = period.split('/')[1]
        until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
        match_meta = MatchMeta.search_range(
            from_date=from_date, until_date=until_date, discipline=discipline,sport=sport,
            town=town, country=country)
        match_id = [match.id for match in match_meta]
    else:
        match_meta = [MatchMeta.search_last(discipline=discipline, sport=sport,
                                           town=town, country=country)]
        match_id = [match.id for match in match_meta if match]
    asked_match = [Match.by_id(id) for id in match_id]

    if not asked_match:
        send_text(sender_id,
                  'In dem angefragten Zeitraum haben keine Wettkämpfe stattgefunden.')
        return

    if not discipline:
        discipline = [match.discipline for match in match_meta]

    if not sport:
        sport = [match.sport for match in match_meta]

    if not isinstance(sport, list):
        sport = [sport] * len(asked_match)

    if not isinstance(discipline, list):
        discipline = [discipline] * len(asked_match)

    send_text(sender_id,
              'Folgende Wintersport-Ergebniss hab ich für dich:')
    for match, meta, sport, discipline in zip(asked_match, match_meta, sport, discipline):
        if asked_match[0].finished == 'yes':
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
                          date='am ' + meta.datetime.date().strftime('%d.%m.%Y') if dtdate.today() != meta.datetime.date() else '',
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
        match_id = [match.id for match in match_meta]
    elif period and not date:
        from_date = period.split('/')[0]
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        until_date = period.split('/')[1]
        until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
        match_meta = MatchMeta.search_range(
            from_date=from_date, until_date=until_date, discipline=discipline,
            sport=sport, town=town, country=country)
        match_id = [match.id for match in match_meta]
    else:
        match_meta = [MatchMeta.search_last(
            discipline=discipline, sport=sport, town=town, country=country)]
        match_id = [match.id for match in match_meta if match]
    asked_match = [Match.by_id(id) for id in match_id]

    if not asked_match:
        send_text(sender_id,
                  'In dem angefragten Zeitraum hat kein Wettkampf in der Disziplin {discipline} '
                  'stattgefunden.'.format(discipline=discipline))
        return

    if not discipline:
        discipline = [match.discipline for match in match_meta]

    if not sport:
        sport = [match.sport for match in match_meta]

    if not isinstance(sport, list):
        sport = [sport] * len(asked_match)

    if not isinstance(discipline, list):
        discipline = [discipline] * len(asked_match)

    if len(asked_match)>1:
        send_text(sender_id,
              'Folgende Wintersport-Ergebniss hab ich für dich:')
    for match, meta, sport, discipline in zip(asked_match, match_meta, sport, discipline):
        if match.finished == 'yes':
            results = match.match_result
            winner_teams = [Team.by_id(winner.team_id) for winner in results[:3]]

            reply = 'Ergebnis beim {sport} {discipline} in {town}, {country}, am {day}, {date}:\n'.format(
                sport='⛷' if sport == 'Ski Alpin' else sport,
                discipline=discipline,
                town=meta.town,
                country=flag(match.venue.country.iso),
                day=int_to_weekday(meta.datetime.weekday()),
                date=meta.datetime.date().strftime('%d.%m.%Y'),
            )

            reply += '\n'.join(
                '{i} {winner}'.format(
                    i=medals(i + 1),
                    winner=' '.join([winner_team.name,
                                     flag(winner_team.country.iso)]))
                for i, winner_team in enumerate(winner_teams))

            send_text(sender_id, reply)
        else:
            send_text(sender_id,
                      'Das Event {sport} {discipline} wurde noch nicht beendet. '
                      'Frage später erneut.'.format(
                          sport=sport,
                          discipline=discipline
                      ))



def medals(int):
    medals = {1: '🥇',
            2: '🥈',
            3: '🥉'
    }
    return medals[int]


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