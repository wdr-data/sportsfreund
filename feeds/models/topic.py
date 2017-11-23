from .. import api
from lib.mongodb import db
from .model import Model


class Topic(Model):
    collection = db.topics
    api_function = api.topic
    api_id_name = 'to'
