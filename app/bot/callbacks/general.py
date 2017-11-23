from ..fb import send_text

def api_sport(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')

    send_text(sender_id,
              'Infos zum '+ sport)


def api_discipline(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    discipline = parameters.get('sport')

    send_text(sender_id,
              'Infos zum '+ discipline)


