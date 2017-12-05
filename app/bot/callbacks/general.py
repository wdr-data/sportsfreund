from ..response import send_text, send_buttons, button_postback

def api_sport(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')

    send_buttons(sender_id,
                 text = sport + ' sagst du? Was magst du wissen?',
                buttons=[
                    button_postback('Letztes Rennen',
                                    ['start']),
                    button_postback('Nächstes Rennen',
                                    ['subsribe']),
                    button_postback('Regel',['info.rules'])
                ]
              )


def api_discipline(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    discipline = parameters.get('discipline')

    send_text(sender_id,
              'Infos zum '+ discipline)


