from .. import api
from lib.mongodb import db
from .model import FeedModel


class Topic(FeedModel):
    collection = db.topics
    api_function = api.topic
    api_id_name = 'to'
