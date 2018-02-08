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
from feeds.config import sport_by_name
from lib.response import button_postback, list_element, button_url


def api_sport(event, parameters,**kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    today = date.today().strftime("%Y-%m-%d")

    result = MatchMeta.search_last(sport=sport)
    calendar = MatchMeta.search_next(sport=sport)
    winner = Person.query(fullname=result.winner_team.name)
    try:
        person_image = Person.get_picture_url(winner[0].id)
    except:
        person_image = None

    try:
        report = get_latest_report(sport=sport)
    except ObjectDoesNotExist:
        report = None

    slug = sport_by_name[sport].slug
    try:
        story = Story.objects.get(slug=slug)
    except ObjectDoesNotExist:
        story = None

    elements=[]
    if result:
        elements.append(
            list_element(f'Ergebnis: {result.discipline_short}, {result.gender_name} vom '
                         f'{result.datetime.strftime("%d.%m.%Y")}',
                         f'gewonnen hat {result.winner_team.name}, '
                         f'{flag(result.winner_team.country.iso)} {result.winner_team.country.code}',
                         image_url=person_image,
                         buttons=[button_postback('Gesamtes Ergebnis', {'podium': sport})],
                         ))

    if calendar:
        elements.append(
            list_element(f'Nächstes {sport_by_name[sport].competition_term}: {calendar.sport} '
                         f'{calendar.discipline_short}, {calendar.gender_name}',
                         f'{day_name[calendar.datetime.weekday()]}, '
                         f'{calendar.datetime.strftime("%d.%m.%Y")} '
                         f'um {localtime_format(calendar.datetime, event)}',
                         image_url=sport_by_name[sport].picture_url,
                         buttons=[button_postback("Was gibt's noch?", {'event_today': today})],
                         ))

    if report:
        elements.append(
            list_element(report.headline, report.text, buttons=[button_postback('Lesen...',
                                                                                {'story': report.slug,
                                                                                 'fragment': None})]))

    if story:
        elements.append(
            list_element(story.name, story.text,
                         image_url=story.media.url,
                         buttons=[button_postback('Lesen...',
                                                  {'story': story.slug, 'fragment': None})]))

    subs = Subscription.query(filter={'sport': sport},
                              image_url=story.media.url,
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


