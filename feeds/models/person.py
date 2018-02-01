from .. import api
from lib.mongodb import db
from .model import FeedModel


class Person(FeedModel):
    collection = db.persons
    api_function = api.person
    api_id_name = 'pe'
    cache_time = 60 * 60 * 24 * 7
