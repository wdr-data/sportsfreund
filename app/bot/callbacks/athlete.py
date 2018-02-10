from datetime import datetime
from time import sleep

from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify

from backend.models import Story

from feeds.models.subscription import Subscription
from lib.facebook import guess_attachment_type
from lib.response import button_postback
from ..handlers.apiaihandler import ApiAiHandler
from feeds.config import KNOWN_ATHLETES_OLYMPIA
from feeds.models.person import Person


def api_characteristics(event, parameters, **kwargs):
    characteristics(event, parameters)


def characteristics(event, payload):
    sender_id = event['sender']['id']
    first_name = payload.get('first_name')
    last_name = payload.get('last_name')

    if last_name and first_name:
        known_athlete_names = set((athlete.first_name, athlete.last_name)
                                   for athlete in KNOWN_ATHLETES_OLYMPIA)

        if (first_name, last_name) not in known_athlete_names:
            if not Person.query(firstname=first_name, surname=last_name):
                if not len(Person.query(surname=last_name)) == 1:
                        event.send_text('Diese Person ist leider noch nicht in meiner Datenbank... '
                                        'Bist du sicher, dass du dich nicht vertippt hast?')
                        return

    elif (last_name and not first_name) or (first_name and not last_name):
        if not len(Person.query(surname=last_name)) == 1:
            event.send_text('Wenn du etwas über einen Athleten erfahren möchtest, '
                            'schicke mir den Vor- und Nachnamen. Nur um Verwechslungen zu vermeiden ;)')
            return

    else:
        event.send_text('Diese Person ist leider noch nicht in meiner Datenbank... '
                        'Bist du sicher, dass du dich nicht vertippt hast?')
        return

    if first_name and last_name:
        athlete = ' '.join([first_name, last_name])
        persons = Person.query(fullname=athlete)
    elif last_name:
        persons = Person.query(surname=last_name)
        athlete = persons[0].fullname

    subs = Subscription.query(filter={'athlete': athlete},
                              type=Subscription.Type.RESULT, psid=sender_id)

    story_exist = False
    story_reply = ''
    reply = ''
    try:
        slug = slugify(athlete)
        story = Story.objects.get(slug=slug)
        story_reply += story.text
        if story.attachment_id:
            media = story.attachment_id
            url = story.media
            event.send_attachment_by_id(str(media), guess_attachment_type(str(url)))
        story_exist = True
    except:
        pass

    for person in persons:
        if story_exist == False:
            try:
                person_url = Person.get_picture_url(id=person.id)
                if person_url:
                    event.send_attachment(person_url)
                    sleep(1)
            except:
                continue

        reply += f"{person.fullname} aus {', '.join([country.name for country in person.country])}"

        if person.get('birthday'):
            birthday_str = datetime.strptime(person.get('birthday'), '%Y-%m-%d').strftime('%d.%m.%Y')
            reply += f"\nGeburtstag: {birthday_str}"
        if person.get('height') and int(person.get('height')) > 0:
            height = int(person.get('height'))/100
            reply += "\nGröße: %.2f m" %height
        if person.get('weight') and int(person.get('weight')) > 0:
            reply += f"\nGewicht: {person.get('weight')} kg"
        if person.get('sport'):
            reply += f"\nSportart{'en' if len(person.sport) > 1 else ''}: " \
                     f"{', '.join([sport.get('name', '') for sport in person.sport])}"

    if subs:
        button_title = 'Abmelden: Sportler'
        button_option = 'unsubscribe'
    else:
        button_title = 'Anmelden: Sportler'
        button_option = 'subscribe'

    if story_exist and not persons:
        event.send_buttons(story_reply,
                          buttons=[button_postback(button_title,
                                                   {"target": "athlete",
                                                    "filter": athlete,
                                                    "option": button_option})])
    elif story_exist and persons:
        event.send_text(reply)
        event.send_buttons(story_reply,
                     buttons=[button_postback(button_title,
                                              {"target": "athlete",
                                               "filter": athlete,
                                               "option": button_option})])
    elif story_exist == False and persons:
        event.send_buttons(reply,
                           buttons=[button_postback(button_title,
                                                    {"target": "athlete",
                                                     "filter": athlete,
                                                     "option": button_option})])
    else:
        event.send_text('Zu dieser Person liegen mir keine Daten vor.')

handlers = [
    ApiAiHandler(api_characteristics, 'athletes.who-is', follow_up=True),
]
