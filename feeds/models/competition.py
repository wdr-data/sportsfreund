from .. import api
from lib.mongodb import db
from .model import FeedModel


class Competition(FeedModel):
    collection = db.competitions
    api_function = api.competition
    api_id_name = 'co'
