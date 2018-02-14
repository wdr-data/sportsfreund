from calendar import day_name
from datetime import date

from django.core.exceptions import ObjectDoesNotExist

from backend.models import Story
from feeds.models.person import Person
from feeds.models.subscription import Subscription
from lib.flag import flag
from lib.time import localtime_format
from .shared import get_latest_report
from feeds.models.match_meta import MatchMeta
from feeds.config import SPORT_BY_NAME
from lib.response import button_postback, list_element, button_url


def api_sport(event, parameters,**kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    today = date.today().strftime("%Y-%m-%d")

    if not sport:
        event.send_text('Über welchen Sport soll ich informieren?')
        return

    result = MatchMeta.search_last(sport=sport)
    person_image = None

    if result.get('winner_team'):
        winner = result.winner_team
        winner_person = Person.query(fullname=winner.name)
        subtitle_result = f'gewonnen hat {result.winner_team.name}, {flag(winner.country.iso)} ' \
                          f'{winner.country.code}'
        try:
            person_image = Person.get_picture_url(winner_person[0].id)
        except:
            pass
    else:
        subtitle_result = 'Schau dir jetzt das gesamte Ergebnis an...'

    calendar = MatchMeta.search_next(sport=sport)

    try:
        report = get_latest_report(sport=sport)
    except ObjectDoesNotExist:
        report = None

    slug = SPORT_BY_NAME[sport].slug
    try:
        story = Story.objects.get(slug=slug)
    except ObjectDoesNotExist:
        story = None

    elements=[]
    if result:
        elements.append(
            list_element(f'Ergebnis: {result.discipline_short}, {result.gender_name} vom '
                         f'{result.datetime.strftime("%d.%m.%Y")}',
                         subtitle_result,
                         image_url=person_image,
                         buttons=[button_postback('Gesamtes Ergebnis', {'podium': sport})],
                         ))

    if calendar:
        elements.append(
            list_element(f'Nächstes {SPORT_BY_NAME[sport].competition_term}: {calendar.sport} '
                         f'{calendar.discipline_short}, {calendar.gender_name}',
                         f'{day_name[calendar.datetime.weekday()]}, '
                         f'{calendar.datetime.strftime("%d.%m.%Y")} '
                         f'um {localtime_format(calendar.datetime, event)}',
                         image_url=SPORT_BY_NAME[sport].picture_url,
                         buttons=[button_postback("Was gibt's noch?", {'event_today': today})],
                         ))

    if report:
        elements.append(
            list_element(report.headline, report.text,
                         image_url=report.media.url if str(report.media) else None,
                         buttons=[button_postback('Lesen...',
                                                  {'report_sport': sport,
                                                   'report_discipline': None})]))

    if story:
        elements.append(
            list_element(story.name, story.text,
                         image_url=story.media.url if str(story.media) else None,
                         buttons=[button_postback('Lesen...',
                                                  {'story': story.slug, 'fragment': None})]))

    subs = Subscription.query(filter={'sport': sport},
                              type=Subscription.Type.RESULT, psid=sender_id)
    if subs:
        button_title = 'Abmelden'
        button_option = 'unsubscribe'
    else:
        button_title = 'Anmelden'
        button_option = 'subscribe'

    if len(elements) > 1:
        event.send_list(elements, button=button_postback(
            button_title, {"target": "sport", "filter": sport, "option": button_option}
        ))
    else:
        event.send_buttons(f'Hier kannst du dich für {sport} anmelden.', button=button_postback(
            button_title, {"target": "sport", "filter": sport, "option": button_option}
        ))


def api_discipline(event,parameters,**kwargs):
    discipline = parameters.get('discipline')

    event.send_text('Infos zum '+ discipline)


