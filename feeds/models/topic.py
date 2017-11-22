from .. import api
from lib.mongodb import client as mongo
from .model import Model

db = mongo.main


class Topic(Model):
    collection = db.topics
    api_function = api.topic
    api_id_name = 'to'
