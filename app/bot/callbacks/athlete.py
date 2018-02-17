from datetime import datetime
from time import sleep

from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify

from backend.models import Story

from bot.callbacks.subscription import (ACT_UNSUBSCRIBE, ACT_SUBSCRIBE, KEY_FILTER, KEY_ACTION,
                                        KEY_SUB)
from feeds.models.subscription import Subscription
from lib.facebook import guess_attachment_type
from lib.response import button_postback, quick_reply
from ..handlers.apiaihandler import ApiAiHandler
from ..handlers.payloadhandler import PayloadHandler
from lib.flag import flag
from feeds.config import KNOWN_ATHLETES_OLYMPIA
from feeds.models.person import Person


def api_characteristics(event, parameters, **kwargs):
    characteristics(event, parameters)


def characteristics(event, payload):
    sender_id = event['sender']['id']
    first_name = payload.get('first_name')
    last_name = payload.get('last_name')
    person_id = payload.get('person_id')

    first_name_query = []
    last_name_query = []

    last_and_first_name_query = Person.query(firstname=first_name, surname=last_name)

    if last_name:
        last_name_query = Person.query(surname=last_name)
    if first_name:
        first_name_query = Person.query(firstname=first_name)

    if last_name and first_name:
        known_athlete_names = set((athlete.first_name, athlete.last_name)
                                   for athlete in KNOWN_ATHLETES_OLYMPIA)

        if (first_name, last_name) not in known_athlete_names:
            if not last_and_first_name_query \
                    and not len(last_name_query) in range(0, 11) \
                    and not len(first_name_query) in range(0, 11):
                    event.send_text('Diese Person ist leider noch nicht in meiner Datenbank... '
                                    'Bist du sicher, dass du dich nicht vertippt hast?')
                    return

    elif (last_name and not first_name) or (first_name and not last_name):
        if not len(last_name_query) in range(0, 11) and not len(first_name_query) in range(0, 11):
            event.send_text('Wenn du etwas über einen Athleten erfahren möchtest, '
                            'schicke mir den Vor- und Nachnamen.'
                            ' Nur um Verwechslungen zu vermeiden ;)')
            return

    else:
        event.send_text('Diese Person ist leider noch nicht in meiner Datenbank... '
                        'Bist du sicher, dass du dich nicht vertippt hast?')
        return

    buttons = []
    quicks = []
    if person_id:
        persons = [Person.query(id=person_id)[0]]
        athlete = persons[0].fullname
    elif last_and_first_name_query == 1:
        athlete = ' '.join([first_name, last_name])
        persons = Person.query(fullname=athlete)
    elif len(last_name_query) == 1:
        persons = last_name_query
        athlete = persons[0].fullname
    elif len(first_name_query) == 1:
        persons = first_name_query
        athlete = persons[0].fullname
    elif len(last_name_query) in [2, 3]:
        buttons = [button_postback(f"{p['fullname']}",
                               {'first_name': p['firstname'],
                                'last_name': p['surname'],
                                'person_id': p['id']})
                   for p in last_name_query]
    elif len(first_name_query) in [2, 3]:
        buttons = [button_postback(f"{p['fullname']}",
                               {'first_name': p['firstname'],
                                'last_name': p['surname'],
                                'person_id': p['id']})
                   for p in first_name_query]
    elif len(last_name_query) in range(4, 11):
        quicks = [quick_reply(f"{p['fullname']}",
                               {'first_name': p['firstname'],
                                'last_name': p['surname'],
                                'person_id': p['id']})
                   for p in last_name_query]
    elif len(first_name_query) in range(4, 11):
        quicks = [quick_reply(f"{p['fullname']}",
                               {'first_name': p['firstname'],
                                'last_name': p['surname'],
                                'person_id': p['id']})
                   for p in first_name_query]
    else:
        event.send_text('--- SportlerIn nicht in meiner Datenbank --- '
                        'Ich schau mir das mal genauer an 🧐. Und schau du mal,'
                        ' ob du den Namen richtig geschrieben hast.')
        return

    if buttons:
        event.send_buttons(f'Wen meinst du?',
                           buttons=buttons
                           )
        return

    if quicks:
        event.send_text(f'Mhmm. Deine Eingabe alles andere als Eindeutig. Wen meinst du? 🤔',
                        quick_replies=quicks)
        return

    subs = Subscription.query(filter={'athlete': athlete}, target=Subscription.Target.ATHLETE,
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
            birthday_str = datetime.strptime(
                person.get('birthday'), '%Y-%m-%d').strftime('%d.%m.%Y')
            reply += f"\nGeburtstag: {birthday_str}"
        if person.get('height') and int(person.get('height')) > 0:
            height = int(person.get('height')) / 100
            reply += "\nGröße: %.2f m" % height
        if person.get('weight') and int(person.get('weight')) > 0:
            reply += f"\nGewicht: {person.get('weight')} kg"
        if person.get('sport'):
            reply += f"\nSportart{'en' if len(person.sport) > 1 else ''}: " \
                     f"{', '.join([sport.get('name', '') for sport in person.sport])}"

    if subs:
        button_title = f'Abmelden: {person.fullname}'
        action = ACT_UNSUBSCRIBE
    else:
        button_title = f'Anmelden: {person.fullname}'
        action = ACT_SUBSCRIBE

    sub_button = button_postback(
        button_title, {
            KEY_SUB: True,
            Subscription.Type.RESULT.value: True,
            KEY_FILTER: athlete,
            KEY_ACTION: action,
        })

    if story_exist and not persons:
        event.send_buttons(story_reply, buttons=[sub_button])

    elif story_exist and persons:
        event.send_text(reply)
        event.send_buttons(story_reply, buttons=[sub_button])

    elif not story_exist and persons:
        event.send_buttons(reply, buttons=[sub_button])

    else:
        event.send_text('Zu dieser Person liegen mir keine Daten vor.')


handlers = [
    ApiAiHandler(api_characteristics, 'athletes.who-is', follow_up=True),
    PayloadHandler(characteristics, ['first_name', 'last_name'])
]
