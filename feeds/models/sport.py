from .. import api
from lib.mongodb import db
from .model import FeedModel


class Sport(FeedModel):
    collection = db.sports
    api_function = api.sport
    api_id_name = 'sp'
