
from ..fb import send_text

def api_winner(event, parameters,**kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')

    send_text(sender_id, 'Hier gibt es bald den gewinner des' + sport + ' '+ discipline)


def api_podium(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')

    send_text(sender_id, 'Hier gibt es bald das Podium des' + sport + ' ' + discipline)