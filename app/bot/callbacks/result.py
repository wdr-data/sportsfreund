import logging

from ..fb import send_text
from feeds.models.match import Match
from feeds.models.team import Team
from feeds.models.match_meta import MatchMeta

logger = logging.Logger(__name__)

OFFSET = 127462 - ord('A')


def flag(code):
    return chr(ord(code[0]) + OFFSET) + chr(ord(code[1]) + OFFSET)


def api_winner(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')

    match_id = MatchMeta.search_last(discipline=discipline or None, sport=sport or None)
    asked_match = Match.by_id(match_id)

    if discipline is None:
        discipline = asked_match.round.name

    if asked_match.finnished == 'yes':
        results = asked_match.match_result

        winner_teams = [Team.by_id(winner.team_id) for winner in results[:3]]

        send_text(sender_id,
                  '{winner} hat das {sport} Rennen in der Disziplin {discipline} '
                  'in {city}, {country} am {date} gewonnen.'.format(
                      winner=' '.join([winner_teams[0].name,
                                       flag(winner_teams[0].country.iso),
                                       winner_teams[0].country.code]),
                      sport=sport,
                      discipline=discipline,
                      city=asked_match.venue.town.name,
                      country=asked_match.venue.country.name,
                      date=asked_match.date.strftime('%d.%m.%Y'),

                  ))
    else:
        send_text(sender_id,
                  'Das Event wurde noch nicht beendet. Frage später erneut.')


def api_podium(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')

    match_meta = MatchMeta.search_last(discipline=discipline or None, sport=sport or None)
    logger.debug('Match ID looking for: ' + str(match_meta.id))
    asked_match = Match.by_id(match_meta.id)

    if discipline is None:
        discipline = asked_match.round.name

    if asked_match.finished == 'yes':
        results = asked_match.match_result
        winner_teams = [Team.by_id(winner.team_id) for winner in results[:3]]

        send_text(sender_id,
                  'Ergebnis beim {discipline} in {city}, {country} am {date}:\n'
                  '1. {winner_1}\n2. {winner_2}\n3. {winner_3}'.format(
                      discipline=discipline,
                      city=asked_match.venue.town.name,
                      country=asked_match.venue.country.name,
                      date=asked_match.date.strftime('%d.%m.%Y'),
                      winner_1=' '.join([winner_teams[0].name,
                                        flag(winner_teams[0].country.iso),
                                        winner_teams[0].country.code]),
                      winner_2=' '.join([winner_teams[1].name,
                                        flag(winner_teams[1].country.iso),
                                        winner_teams[1].country.code]),
                      winner_3=' '.join([winner_teams[2].name,
                                        flag(winner_teams[2].country.iso),
                                        winner_teams[2].country.code]),
                  ))
    else:
        send_text(sender_id,
                  'Das Event wurde noch nicht beendet. Frage später erneut.')
