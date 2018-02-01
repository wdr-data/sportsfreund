from .. import api
from lib.mongodb import db
from .model import FeedModel


class Person(FeedModel):
    collection = db.persons
    api_function = api.person
    api_id_name = 'pe'
    cache_time = 60 * 60 * 24 * 7

    @classmethod
    def by_id(cls, id, topic_id, additional_data=None, clear_cache=False):
        return super(Person, cls).by_id(id, clear_cache, {'to': topic_id}, additional_data)

    @classmethod
    def transform(cls, person):
        sport = person['sport']
        person = person['person']
        person['sport'] = sport

        return person
