from datetime import datetime
from calendar import day_name

from django.core.exceptions import ObjectDoesNotExist

from backend.models import Push, Report, Info, Story
from feeds.models.match_meta import MatchMeta
from feeds.models.match import Match
from feeds.models.person import Person
from feeds.config import sport_by_name
from feeds.models.medals_table import MedalsTable
from lib.flag import flag
from lib.time import localtime_format
from ..handlers.apiaihandler import ApiAiHandler
from ..handlers.payloadhandler import PayloadHandler
from lib.response import (button_postback, quick_reply, generic_element,
                          button_web_url, button_share, button_url, list_element)
from .shared import get_push, schema, send_push, get_pushes_by_date, get_latest_report, send_report


def api_news(event, parameters, **kwargs):
    date = parameters.get('date')

    if not date:
        push = get_push(force_latest=True)
    else:
        if len(date) == 1:
            find_date = datetime.strptime(date[0], '%Y-%m-%d').date()
            pushes = get_pushes_by_date(find_date)
            push = pushes[0]
        else:
            push = None

    news_list = []

    result = MatchMeta.search_last(medals='all')

    person_image = None

    if result.get('winner_team'):
        winner = result.winner_team
        subtitle_result = f'{Match.medal(1)} {result.winner_team.name}, {flag(winner.country.iso)} ' \
                          f'{winner.country.code}'
    else:
        subtitle_result = 'Schau dir jetzt das gesamte Ergebnis an...'

    if result.get('winner_team'):
        try:
            winner_person = Person.query(fullname=winner.name)
            person_image = Person.get_picture_url(winner_person[0].id)
        except:
            pass

    calendar = MatchMeta.search_next(medals='all')

    try:
        report = get_latest_report()
    except ObjectDoesNotExist:
        report = None

    # setze medaillienspiegel

    elements = []
    if result:
        elements.append(
            list_element(f'Letzte Goldmedaille: {result.sport} {result.discipline_short}, '
                         f'{result.gender_name}',
                         f'{subtitle_result}',
                         image_url=person_image,
                         buttons=[button_postback('Gesamtes Ergebnis', {'podium': result.sport})],
                         ))

    if calendar:
        elements.append(
            list_element(f'Nächste Medaille-Entscheidung: '
                         f'{calendar.sport} '
                         f'{calendar.discipline_short}, {calendar.gender_name}',
                         f'{day_name[calendar.datetime.weekday()]}, '
                         f'{calendar.datetime.strftime("%d.%m.%Y")} '
                         f'um {localtime_format(calendar.datetime, event)}',
                         image_url=sport_by_name[calendar.sport].picture_url,
                         buttons=[button_postback(f'Was geht am '
                                                  f'{calendar.datetime.strftime("%d.%m.")}',
                                                  {'event_today': calendar.match_date})],
                         ))

    first = MedalsTable.top(number=1)[0]

    elements.append(
        list_element('Aktueller Stand im Medaillenspiegel',
                     f'1. {first.country.name}  {Match.medal(1)} {first.first} '
                     f'{Match.medal(2)} {first.second} {Match.medal(3)} {first.third}',
                     buttons=[button_postback('Anschauen 😍',
                                              {'pl_medals_table': None,
                                               'country': 'Deutschland',
                                               'event': 'owg18'})]))

    if report:
        elements.append(
            list_element(report.headline, report.text,
                         image_url=report.media.url if str(report.media) else None,
                         buttons=[button_postback('Lesen...',
                                                  {'report_sport': None,
                                                   'report_discipline': None})]))

    event.send_text('Bitte schön, hier kommt deine Übersicht:')
    event.send_list(elements,
                    button=button_postback('Weitere Meldungen', ['more_reports'])
                    )


def more_reports(event, payload):

    reports = Report.last(count=4, only_published=True, delivered=True, by_date=False)
    event.send_text('Die letzten Meldungen auf einen Blick 👀')
    event.send_list([
        list_element(
            f'{r.sport if r.sport else ""} - {str(r)}',
            subtitle=f'{r.text[:80]}',
            image_url=r.media.url if str(r.media) else None,
            buttons=[button_postback('Weiterlesen',
                                     {'report': r.id, 'next_state': 'headline'})])
        for r in reports
    ])


handlers = [
    ApiAiHandler(api_news, 'push.highlight'),
    PayloadHandler(more_reports, ['more_reports'])
]