from ..handlers.payloadhandler import PayloadHandler
from ..handlers.apiaihandler import ApiAiHandler
from feeds.models.standing import Standing
from feeds.models.match_meta import MatchMeta
from lib.response import button_postback, quick_reply, list_element
from lib.flag import flag


def api_match_standing(event, parameters, **kwargs):
    gender = parameters.get('gender')
    sport = parameters.get('sport')
    round_mode = parameters.get('round_mode')

    sports_with_standing = ['Curling', 'Eishockey']

    if sport and sport not in sports_with_standing:
        event.send_text(f'Im {sport} gibt es keine Gruppenphase. Suche direkt nach dem Ergebnis')
        return

    if not sport and round_mode == 'Round Robin':
        sport = 'Curling'

    if sport == 'Eishockey' and round_mode == 'Gruppe C':
        gender = 'male'

    if round_mode in ['Gruppe A', 'Gruppe B', 'Gruppe C']:
        sport = 'Eishockey'

    if gender == 'mixed':
        sport = 'Curling'
        round_mode = 'Round Robin'

    if sport == 'Eishockey' and not round_mode and not gender:
        gender = 'female'

    if sport and gender and round_mode:
        get_standing(event, {'sport': sport,
                             'round_name': round_mode,
                             'gender': gender}
                     )
        return


    if not sport and not round_mode:
        event.send_text(f'Eishockey oder Curling?')
        return
    elif sport and round_mode and not gender:
        buttons = [button_postback('Herren',
                                   {'sport': sport,
                                    'round_name': round_mode,
                                    'gender': 'male'}
                                   ),
                   button_postback('Damen',
                                   {'sport': sport,
                                    'round_name': round_mode,
                                    'gender': 'female'}
                                   )
                   ]
        if sport == 'Curling':
            buttons.append(button_postback('Mixed',
                                       {'sport': sport,
                                            'round_name': round_mode,
                                            'gender': 'mixed'}
                                           ))

        event.send_buttons('Welche Tabelle möchtest du sehen?',
                            buttons=buttons
                            )

    elif sport and gender and not round_mode:
        if sport == 'Curling':
            round_mode = 'Round Robin'
        elif sport == 'Eishockey':
            buttons = [button_postback('Gruppe A',
                                       {'sport': sport,
                                        'round_name': 'Gruppe A',
                                        'gender': gender}),
                       button_postback('Gruppe B',
                                       {'sport': sport,
                                        'round_name': 'Gruppe B',
                                        'gender': gender}),
                       ]
            if gender == 'male':
                buttons.append(
                    button_postback('Gruppe C',
                                    {'sport': sport,
                                     'round_name': 'Gruppe C',
                                     'gender': gender})
                )
        event.send_buttons(f'Schau dir die Tabelle im Eishockey der {gender} an',
                            buttons=buttons)
        return

    get_standing(event, {'sport': sport,
                         'round_name': round_mode,
                         'gender': gender}
                         )

def get_standing(event, payload):
    sport = payload['sport']
    gender = payload['gender']
    round_name = payload['round_name']

    meta = MatchMeta.search_next(sport=sport, gender=gender, round_mode=round_name)
    if meta:
        season_id = meta.season_id
        send_standing(event, {'season_id': season_id, 'round_name': round_name,
                              'sport': sport, 'gender': meta.gender_name})
    else:
        event.send_text('Die Kombination funktioniert so nicht.')
        return


def send_standing(event, payload):
    round_name = payload['round_name']
    season_id = payload['season_id']
    sport = payload['sport']
    gender = payload['gender']

    standing = Standing.by_season_round(season_id, round_name)
    if sport == 'Curling':
        reply = '🥌 '
    else:
        reply = ''
    reply += f'{round_name}, {sport} {gender}\n'
    for m in standing:
        reply += f"\n{m['rank']}. {m['team']['name']} {flag(m['team']['country']['iso'])} " \
                 f" {m['win']}|{m['matches']} " \
                 f" {'+' if int(m['difference'])>0 else ''}{m['difference']}"

    event.send_text(reply)


handlers = [
    ApiAiHandler(api_match_standing, 'result.match.standing', follow_up=True),
    PayloadHandler(send_standing, ['season_id', 'round_name', 'sport', 'gender']),
    PayloadHandler(get_standing, ['sport', 'gender', 'round_name']),
]
