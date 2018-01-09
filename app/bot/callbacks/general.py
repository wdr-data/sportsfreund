from lib.response import button_postback

def api_sport(event,parameters,**kwargs):
    sport = parameters.get('sport')

    event.send_buttons(text = sport + ' sagst du? Was magst du wissen?',
                buttons=[
                    button_postback('Letztes Rennen',
                                    ['start']),
                    button_postback('Nächstes Rennen',
                                    ['subsribe']),
                    button_postback('Regel',['info.rules'])
                ]
              )


def api_discipline(event,parameters,**kwargs):
    discipline = parameters.get('discipline')

    event.send_text('Infos zum '+ discipline)


