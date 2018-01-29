import logging
from datetime import date as dtdate
from datetime import datetime, timedelta
from calendar import day_name

from lib.model import Model
from ..handlers.payloadhandler import PayloadHandler
from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from feeds.models.team import Team
from feeds.config import supported_sports, sport_by_name
from lib.flag import flag
from lib.response import button_postback, quick_reply

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
        event.send_text('Meine Datenbank ist voll mit Ergebnissen.'
                        ' Welche Sportart interessiert dich?')
        sports_to_choose = ''
        for i, sportname in enumerate(supported_sports):
            if i == len(supported_sports) - 1:
                sports_to_choose += f'oder {sportname}?'
            else:
                sports_to_choose += f'{sportname}, '
        event.send_text(sports_to_choose)
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
        event.send_text('In diesem Zeitraum haben keine Wettkämpfe stattgefunden.')
        return

    if not discipline:
        discipline = [match.discipline for match in match_meta]

    if not sport:
        sport = [match.sport for match in match_meta]

    if not isinstance(sport, list):
        sport = [sport] * len(asked_matches)

    if not isinstance(discipline, list):
        discipline = [discipline] * len(asked_matches)

    event.send_text('Folgende Wintersport-Ergebnisse habe ich für dich:')
    for match, meta, sport, discipline in zip(asked_matches, match_meta, sport, discipline):
      ## Event postponed oder cancelled: 
        if match.match_incident:
            event.send_text(f"""{meta.match_incident.name}: 
{discipline} in {meta.town} am {meta.datetime.date().strftime('%d.%m.%Y')}""")
        elif asked_matches[0].finished:
            results = match.match_result
            winner_team = results[0].team

            event.send_buttons('{winner} hat {today} das {sport} {competition_term} in der Disziplin '
                               '{discipline} in {town}, {country} {date} gewonnen.'.format(
                winner=' '.join([winner_team.name,
                                           flag(winner_team.country.iso),
                                           winner_team.country.code]),
                          sport=sport,
                          discipline=meta.discipline_short,
                          town=meta.town,
                          country=meta.country,
                          date='am ' + meta.datetime.date().strftime('%d.%m.%Y')
                          if dtdate.today() != meta.datetime.date() else '',
                          competition_term=sport_by_name[sport].competition_term,
                          today='heute' if dtdate.today() == meta.datetime.date() else ''),
                          buttons=[match.btn_podium]
                                )
        else:
            event.send_text('Das Event {sport} {discipline} ist noch nicht beendet. '
                      'Frag bitte später noch mal. Wenn Du mir "Für " + {sport} + " anmelden" schreibst, melde ich mich, wenn ich das Ergebnis habe'.format(
                          sport=sport,
                          discipline=meta.discipline_short
                      ))


def api_podium(event, parameters, **kwargs):
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    date = parameters.get('date')
    period = parameters.get('date-period')
    town = parameters.get('town')
    country = parameters.get('country')
    gender = parameters.get('gender')

    if date:
        date = datetime.strptime(date, '%Y-%m-%d').date()
        if date > dtdate.today():
            date = date.replace(date.year - 1)
            if date.day == 29 and date.month == 2 and date.year % 4 != 0:
                event.send_text('Nice try, aber wir befinden und nicht in einem Schaltjahr. 😎')
                return

        match_meta = MatchMeta.search_date(
            date=date, discipline=discipline, sport=sport, town=town,
            country=country, gender=gender)
    elif period and not date:
        from_date = period.split('/')[0]
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        until_date = period.split('/')[1]
        until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
        match_meta = MatchMeta.search_range(
            from_date=from_date, until_date=until_date, discipline=discipline,
            sport=sport, town=town, country=country, gender=gender)
    elif town or country:
        match_meta = MatchMeta.search_range(
            until_date=dtdate.today(), discipline=discipline, sport=sport,
            town=town, country=country, gender=gender)
    else:
        match_meta = [MatchMeta.search_last(
            discipline=discipline, sport=sport, town=town, country=country, gender=gender)]

    match_ids = [match.id for match in match_meta if match]

    if not match_ids:
        event.send_text('In diesem Zeitraum hat kein Event stattgefunden.')
        return

    result_podium(event, {'result_podium': match_ids})


def result_podium(event, payload):
    # payload is list of match_ids
    match_ids = payload['result_podium']
    match_meta = [MatchMeta.by_match_id(match_id) for match_id in match_ids]
    asked_matches = [Match.by_id(id) for id in match_ids]

    discipline = [match.discipline for match in match_meta]

    sport = [match.sport for match in match_meta]

    if len(asked_matches)>1:
        event.send_text('Bitteschön:')

    for match, meta, sport, discipline in zip(asked_matches, match_meta, sport, discipline):
        if match.match_incident:
            event.send_text(f'{match.match_incident.name}: '
                            f'{meta.discipline_short}, {meta.gender_name}'
                            f'in {meta.town}')
        elif match.finished:

            event.send_list(
                match.lst_podium,
                top_element_style='large',
                button=match.btn_podium
            )

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
    match = Match.by_id(match_id)

    if step == 'top_10':
        results = match.results[:10]
        button = button_postback('Und der Rest?', {'result_total': match_id, 'step': None})
        result_kind = 'Top 10'
    else:
        results = match.results[11:]
        button = None
        result_kind = 'restliche Ergebnisse'

    teams = [result.team for result in results]

    top_ten = '\n'.join(
        f'{r.rank}. {t.name} {flag(t.country.iso)} {t.country.code} {match.txt_points(r)}'
        for r, t in zip(results, teams))

    if button:
        event.send_buttons(f'Hier die {result_kind} zu {match.meta.sport}'
                           f' {match.meta.discipline_short} '
                           f'in {match.meta.town}, {match.meta.country}: \n\n{top_ten}',
                           buttons=[button])
    else:
        event.send_text(f'Hier die {result_kind} zu {match.meta.sport} '
                        f'{match.meta.discipline_short} '
                        f'in {match.meta.town}, {match.meta.country}: \n\n{top_ten}')


def result_by_country(event, payload):
    country_name = payload['result_by_country']
    match_id = payload['match_id']

    if not country_name:
        match = Match.by_id(match_id)
        countries_all = [result.team.country for result in match.results]
        countries = [ii for n, ii in enumerate(countries_all) if ii not in countries_all[:n]]

        quick = [quick_reply(f'{flag(c.iso)} {c.code}',
                             {'result_by_country' : c.name, 'match_id': match_id})
                 for c in countries[:11]]

        event.send_text('Welches Land möchtest du?',
                        quick_replies=quick)
        return

    match = Match.by_id(match_id)
    results_all = match.results_by_country(country_name)
    results = []
    for r in results_all:
        results.append(r)
        
    if not results:
        event.send_text(f'Kein Athlet aus {flag(country.iso)} {country.code}'
                        f' hat das {sport_by_name[sport].competition_term} beendet.')
        return

    teams = [result.team for result in results]
    country = teams[0].country

    athletes_by_country = '\n'.join(
        f'{r.rank}. {t.name} {match.txt_points(r)}'
        for r, t in zip(results, teams))

    event.send_text(f'Hier die Ergebnisse aus {flag(country.iso)} {country.code} '
                    f'in {match.meta.town}: \n\n{athletes_by_country}')


handlers = [
    PayloadHandler(result_details, ['result_details']),
    PayloadHandler(result_by_country, ['result_by_country', 'match_id']),
    PayloadHandler(result_total, ['result_total', 'step']),
]
