from .. import api
from lib.mongodb import db
from .model import FeedModel


class Venue(FeedModel):
    collection = db.venues
    api_function = api.venue
    api_id_name = 've'
    cache_time = 60 * 60 * 24
