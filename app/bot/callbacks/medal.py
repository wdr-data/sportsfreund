from feeds.models.medal import Medal
from feeds.models.match import Match

from itertools import zip_longest
from datetime import datetime


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def medals(event, parameters, **kwargs):
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    gender = parameters.get('gender')
    country = parameters.get('country')
    date = parameters.get('date')

    if date:
        date = datetime.strptime(date, '%Y-%m-%d').date()
        medals = Medal.search_date(date=date, sport=sport,
                                   discipline=discipline, gender=gender, country=country)
    else:
        medals = Medal.search_last(sport=sport, discipline=discipline,
                                   gender=gender, country=country)

    if not medals:
        event.send_text('In diesem Zeitraum hat kein Event stattgefunden '
                        'oder es wurde noch nicht beendet')
        return

    elif len(medals) > 9:
        event.send_text('Ich habe zu viele Medaillentscheidungen zu deiner Suchanfrage gefunden, '
                        'als dass ich sie jetzt alle anzeigen könnte. Schränke deine Frage ein, '
                        'z.B. nach Sportart, Datum oder Herren/Damen.')

    else:
        medalsets = grouper(medals, 3)
        for set in medalsets:
            winner = '\n'.join(
                '{i} {winner}'.format(
                    i=Match.medal(i + 1),
                    winner=' '.join([member.team.name,
                                     member.team.country.code]))
                for i, member in enumerate(set))

            event.send(f'Medaillen für {sport} {discipline} {gender} am {date}: \n'
                       f'{winner}'.format(
                sport = set.sport,
                discipline = set.discipline_short,
                gender = set.gender,
                date = set.end_date,
                winner = winner,
            ))
