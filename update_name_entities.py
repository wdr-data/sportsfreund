from enum import Enum

from lib.dialogflow_api import api_call, add_entry


class Entity(Enum):
    FIRST_NAME = 'first_name'
    LAST_NAME = 'last_name'


def get_entity_uuid(entity: Entity):
    entities = api_call('entities')

    for e in entities:
        if e['name'] == entity.value:
            return e['uuid']
