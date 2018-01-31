from feeds.models.medal import Medal
from feeds.models.match import Match

from itertools import zip_longest
from datetime import datetime

from feeds.models.team import Team
from lib.flag import flag


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
        medals = [Medal.search_last(sport=sport, discipline=discipline,
                                   gender=gender, country=country)]

    if not medals:
        event.send_text('In diesem Zeitraum hat kein Event stattgefunden '
                        'oder es wurde noch nicht beendet')
        return

    else:
        for medal in medals:
            winner = '\n'.join(
                '{i} {winner}'.format(
                    i=Match.medal(i + 1),
                    winner=' '.join([member.team.name,
                                     flag(Team.by_id(member.team.id).country.iso)]))
                for i, member in enumerate(medal.ranking))

            event.send_text(
                'Medaillen für {sport}{discipline} {gender} am {date}: \n\n{winner}'.format(
                    sport=medal.sport,
                    discipline=f' {medal.discipline_short}' if medal.discipline_short else '',
                    gender=medal.gender_name,
                    date=medal.end_date.strftime('%d.%m.%Y'),
                    winner=winner,
                )
            )
