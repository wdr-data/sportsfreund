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

    if not discipline and not sport:
        send_text(sender_id,
                  'Gewonnen? Biathlon oder Ski Alpin?')
        return

    match_meta = MatchMeta.search_last(discipline=discipline or None, sport=sport or None)
    asked_match = Match.by_id(match_meta.id)

    if not discipline:
        discipline = match_meta.discipline

    if not sport:
        sport = match_meta.sport

    if asked_match.finished == 'yes':
        results = asked_match.match_result

        winner_team = Team.by_id(results[0].team_id)

        send_text(sender_id,
                  '{winner} hat das {sport} Rennen in der Disziplin {discipline} '
                  'in {town}, {country} am {date} gewonnen.'.format(
                      winner=' '.join([winner_team.name,
                                       flag(winner_team.country.iso),
                                       winner_team.country.code]),
                      sport=sport,
                      discipline=discipline,
                      town=match_meta.town,
                      country=match_meta.country,
                      date=match_meta.datetime.date().strftime('%d.%m.%Y'),

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

    if not discipline:
        discipline = match_meta.discipline

    if not sport:
        sport = match_meta.sport

    if asked_match.finished == 'yes':
        results = asked_match.match_result
        winner_teams = [Team.by_id(winner.team_id) for winner in results[:3]]

        reply = 'Ergebnis beim {discipline} in {town}, {country} am {date}:\n'.format(
            discipline=discipline,
            town=match_meta.town,
            country=match_meta.country,
            date=match_meta.datetime.date().strftime('%d.%m.%Y'))

        reply += '\n'.join(
            '{i}. {winner}'.format(
                i=i + 1,
                winner=' '.join([winner_team.name,
                                 flag(winner_team.country.iso),
                                 winner_team.country.code]))
            for i, winner_team in enumerate(winner_teams))

        send_text(sender_id, reply)
    else:
        send_text(sender_id,
                  'Das Event wurde noch nicht beendet. Frage später erneut.')
