from feeds.models.medal import Medal
from feeds.models.medals_table import MedalsTable
from feeds.models.match import Match
from lib.response import button_postback, quick_reply
from ..handlers.payloadhandler import PayloadHandler

from itertools import zip_longest
from datetime import datetime, date

from feeds.models.team import Team
from lib.flag import flag


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def send_medal_by_id(event, payload, **kwargs):
    medal_id = payload.get('send_medal')
    quick = payload.get('send_quick')
    medals(event, parameters={'medal_id': medal_id, 'send_quick': quick})


def medals(event, parameters, **kwargs):
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    gender = parameters.get('gender')
    country = parameters.get('country')
    asked_date = parameters.get('date')
    medal_id = parameters.get('medal_id')
    send_quick = parameters.get('send_quick')

    today = date.today()
    quick_replies = [quick_reply('🥇🥈🥉- Spiegel',
                                 {'country': None,
                                  'event': None,
                                  'pl_medals_table': None}
                                 )]

    if asked_date:
        asked_date = datetime.strptime(asked_date, '%Y-%m-%d').date()
        medals = Medal.search_date(date=asked_date, sport=sport,
                                   discipline=discipline, gender=gender, country=country)
        if len(medals) > 3:
            for medal in medals[3:]:
                quick_replies.append(
                    quick_reply(f'{medal.sport}, {medal.gender_name}',
                                {'send_medal': medal.id, 'send_quick': True})
                )
    elif medal_id:
        medals = [Medal.by_id(id=medal_id)]
        if send_quick == True:
            medals_today = Medal.search_date(date=today)

            if medals_today:
                medals_today[:] = [medal for medal in medals_today if
                                   medal.get('id') != medals[0].id]
                for medal in medals_today:
                    quick_replies.append(
                        quick_reply(f'{medal.sport}, {medal.gender_name}',
                                    {'send_medal': medal.id, 'send_quick': True})
                    )
    else:
        medals = [Medal.search_last(sport=sport, discipline=discipline,
                                   gender=gender, country=country)]
        medals_today = Medal.search_date(date=today)

        if medals_today:
            medals_today[:] = [medal for medal in medals_today if medal.get('id') != medals[0].id]
            for medal in medals_today:
                quick_replies.append(
                    quick_reply(f'{medal.sport}, {medal.gender_name}',
                                {'send_medal': medal.id, 'send_quick': True})
                )

    if not medals:
        event.send_text('In diesem Zeitraum hat kein Event stattgefunden '
                        'oder es wurde noch nicht beendet',
                        quick_replies=quick_replies)
        return

    else:
        count = 0
        for medal in medals:
            winner = '\n'.join(
                '{i} {winner}'.format(
                    i=Match.medal(i + 1),
                    winner=' '.join([member.team.name,
                                     flag(Team.by_id(member.team.id).country.iso)]))
                for i, member in enumerate(medal.ranking))

            reply = 'Medaillen für {sport} {discipline} {gender} am {date}: \n\n{winner}'.format(
                    sport=medal.sport,
                    discipline=f' {medal.discipline_short}' if medal.discipline_short else '',
                    gender=medal.gender_name,
                    date=medal.end_date.strftime('%d.%m.%Y'),
                    winner=winner,
                )

            if len(medals) <= 3:
                event.send_text(reply)
            elif len(medals) > 3 and count < 3:
                event.send_text(reply)
            else:
                break

            count += 1

        if quick_replies:
            event.send_text('Hier findest du weitere Medaillenentscheidungen des Tages:',
                            quick_replies)


def medals_table(event, parameters, **kwargs):
    country = parameters.get('country')
    olympic_event = parameters.get('event')

    if country:
        if olympic_event == 'owg14':
            medals = MedalsTable.by_country(country=country, topic_id='548')
        else:
            medals = MedalsTable.by_country(country=country)

        quicks = [quick_reply('🥇🥈🥉- Spiegel',
                     {'country': None,
                      'event': None,
                      'pl_medals_table': None}
                     )
         ]

        if not medals:
            event.send_text(f'{country} hat noch keine Medaillen gewonnen. '
                            f'Mal sehen wie sich das entwickelt... 🤞🏼',
                            quick_replies=quicks)
            return

        event.send_text(
            f'{country} im Medaillenspiegel:\nPlatz {medals.rank}\n'
            f'{str(medals.first)} Gold {Match.medal(1)}\n'
            f'{str(medals.second)} Silber {Match.medal(2)}\n'
            f'{str(medals.third)} Bronze {Match.medal(3)}',
            quick_replies=quicks
        )

    else:
        if olympic_event == 'owg14':
            medals = MedalsTable.top(number=10, topic_id='548')
            total_medals = MedalsTable.with_medals(topic_id='548')
        else:
            total_medals = MedalsTable.with_medals()
            if not total_medals:
                event.send_text('Noch hat bei den Olympischen Winterspielen in PyeongChang niemand '
                                'eine Medaille gewonnen. Es bleibt spannend...')
                return
            elif len(total_medals) <= 10:
                medals = MedalsTable.with_medals()
            else:
                medals = MedalsTable.top(number=10)

        if medals:
            country_rank = '\n'.join(
                f'{str(m.rank)}. {m.country.name}:'
                f'{Match.medal(1)} {m.first} '
                f'{Match.medal(2)} {m.second} '
                f'{Match.medal(3)} {m.third}'
            for m in medals)

        if len(total_medals) > 10:
            event.send_buttons(f'{country_rank}',
                            buttons=[button_postback('Und der Rest?',
                                                     {'medal_list': olympic_event})])
        else:
            reply = country_rank
            reply += '\nAlle anderen teilnehmenden Länder haben noch keine Medaillen gewonnen.'
            event.send_text(reply)


def medal_list(event, payload):
    olympic_event = payload.get('medal_list')

    if olympic_event == 'owg14':
        medals = MedalsTable.with_medals(topic_id='548')
    else:
        medals = MedalsTable.with_medals()

    if medals:
        country_rank = '\n'.join(
            f'{str(m.rank)}. {m.country.name}:'
            f'{Match.medal(1)} {m.first} '
            f'{Match.medal(2)} {m.second} '
            f'{Match.medal(3)} {m.third}'
            for m in medals[10:])

        event.send_text(f'{country_rank}')
        event.send_text(f'Alle anderen teilnehmenden Länder haben noch keine Medaillen gewonnen.')


handlers= [
    PayloadHandler(pl_medals_table, ['pl_medals_table', 'country', 'event']),
    PayloadHandler(medal_list, ['medal_list']),
    PayloadHandler(send_medal_by_id, ['send_medal', 'send_quick']),
]
