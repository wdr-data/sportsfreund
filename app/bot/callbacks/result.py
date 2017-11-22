from ..fb import send_text
from feeds.models.match import Match

import logging
logger = logging.Logger(__name__)

match = Match()


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
    for result in results:
        if int(result['rank']) <= 3 and int(result['match_result_at']) == 0:
            podium.append(result['team_id'])

    send_text(sender_id, 'Im ' +sport + ' haben in der Disziplin ' + discipline + ' folgende Atheten die ersten drei Plätze belegt:\n' + str(podium))
