from .. import api
from lib.mongodb import db
from .model import FeedModel


class Team(FeedModel):
    collection = db.teams
    api_function = api.team
    api_id_name = 'te'
