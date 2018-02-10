from enum import Enum
from time import sleep

from lib.dialogflow_api import api_call, add_entry
from feeds.models.person import Person


class Entity(Enum):
    FIRST_NAME = 'first_name'
    LAST_NAME = 'last_name'


def get_entity_uuid(entity: Entity):
    entities = api_call('entities')

    for e in entities:
        if e['name'] == entity.value:
            return e['id']


def main():
    added_first_names = set()
    added_last_names = set()

    first_name_uuid = get_entity_uuid(Entity.FIRST_NAME)
    last_name_uuid = get_entity_uuid(Entity.LAST_NAME)

    def add_person(person_):
        first_name = person_.firstname
        last_name = person_.surname
        if first_name not in added_first_names:
            print('Adding first_name', first_name, '\n', add_entry(first_name, first_name_uuid))
            added_first_names.add(first_name)
            sleep(2.5)
        else:
            print(f'Skipping already added name {first_name}')
        if last_name not in added_last_names:
            print('Adding last_name', last_name, '\n', add_entry(last_name, last_name_uuid))
            added_last_names.add(last_name)
            sleep(2.5)
        else:
            print(f'Skipping already added name {last_name}')

    existing_first_names = {
        entry['value']
        for entry in
        api_call('entities', id=first_name_uuid)['entries']
    }

    existing_last_names = {
        entry['value']
        for entry in
        api_call('entities', id=last_name_uuid)['entries']
    }

    added_first_names |= existing_first_names
    added_last_names |= existing_last_names

    print(len(added_first_names), 'first names on dialogflow')
    print(len(added_last_names), 'last names on dialogflow')

    persons = Person.query()

    for person in persons:
        while True:
            try:
                add_person(person)
                break
            except ValueError as e:
                print(e)
                print('Waiting 30 seconds for retrying...')
                sleep(30)


if __name__ == '__main__':
    main()
