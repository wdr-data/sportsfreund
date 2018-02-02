from datetime import datetime

from ..handlers.apiaihandler import ApiAiHandler
from feeds.config import GERMAN_ATHLETES_OLYMPIA
from feeds.models.person import Person

def api_characteristics(event, parameters, **kwargs):
    characteristics(event, parameters)


def characteristics(event, payload):
    first_name = payload.get('first_name')
    last_name = payload.get('last_name')
    athlete = None

    if last_name and first_name:
        german_athlete_names = set((athlete.first_name, athlete.last_name)
                                   for athlete in GERMAN_ATHLETES_OLYMPIA)

        if (first_name, last_name) not in german_athlete_names:
            if not Person.query(firstname=first_name, surname=last_name):
                event.send_text('Diese Person ist leider noch nicht in meiner Datenbank... '
                                'Bist du sicher, dass du dich nicht vertippt hast?')
                return

        athlete = ' '.join([first_name, last_name])

    elif (last_name and not first_name) or (first_name and not last_name):
        event.send_text('Wenn du etwas über einen Athleten erfahren möchtest, '
                        'schicke mir den Vor- und Nachnamen. Nur um Verwechslungen zu vermeiden ;)')
        return

    persons = Person.query(fullname=athlete)
    for person in persons:
        reply = f"{person.fullname} aus {', '.join([country.name for country in person.country])}"

        if person.get('birthday'):
            birthday_str = datetime.strptime(person.get('birthday'), '%Y-%m-%d').strftime('%d.%m.%Y')
            reply += f"\nGeburtstag: {birthday_str}"
        if person.get('size'):
            reply += f"\nGröße: {person.get('height')}"
        if person.get('weight'):
            reply += f"\nGewicht: {person.get('weight')}"
        if person.get('sport'):
            reply += f"\nSportart{'en' if len(person.sport) > 1 else ''}: " \
                     f"{', '.join([sport.get('name', '') for sport in person.sport])}"

        event.send_text(reply)


handlers = [
    ApiAiHandler(api_characteristics, 'athletes.who-is'),
]
