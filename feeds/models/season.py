from .. import api
from lib.mongodb import db
from .model import FeedModel


class Season(FeedModel):
    collection = db.seasons
    api_function = api.season
    api_id_name = 'se'
