import logging
from datetime import datetime

from ..fb import send_text
from feeds.models.match import Match
from feeds.models.team import Team

logger = logging.Logger(__name__)

match = Match()
team = Team()

OFFSET = 127462 - ord('A')


def flag(code):
    return chr(ord(code[0]) + OFFSET) + chr(ord(code[1]) + OFFSET)

def api_winner(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')

    send_text(sender_id, 'Hier gibt es bald den Gewinner des ' + sport + ' '+ discipline)


def api_podium(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    #discipline = parameters.get('discipline')

    asked_match = match.by_id(8471268)
    podium = []

    discipline = asked_match['round']['name']
    results = asked_match['match_result']
    podium = results[:3]
    winner_teams = []

    date = datetime.strptime(asked_match['match_date'], '%Y-%m-%d')

    for winner in podium:
        winner_teams.append(team.by_id(winner['team_id']))

    logger.info('Found winner as follows '+str(winner_teams[0]['name'])+' '+str(winner_teams[1]['name'])+' '+str(winner_teams[2]['name']))

    send_text(sender_id,
              'Ergebnis beim {sport} {discipline} in {city}, {country} am {date}:\n' \
                '1. {winner_1}\n2. {winner_2}\n3. {winner_3}'.format(
                  sport = sport,
                  discipline = discipline,
                  city = asked_match['venue']['town']['name'],
                  country = asked_match['venue']['country']['name'],
                  date = date.strftime('%d.%m.%Y'),
                  winner_1 = ' '.join([winner_teams[0]['name'],
                                      flag(winner_teams[0]['country']['iso']),
                                      winner_teams[0]['country']['code']]),
                  winner_2 = ' '.join([winner_teams[1]['name'],
                                      flag(winner_teams[1]['country']['iso']),
                                      winner_teams[1]['country']['code']]),
                  winner_3 = ' '.join([winner_teams[2]['name'],
                                      flag(winner_teams[2]['country']['iso']),
                                      winner_teams[2]['country']['code']]),
              ))
