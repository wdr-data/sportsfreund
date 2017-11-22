from .. import api
from lib.mongodb import client as mongo
from .model import Model

db = mongo.main


class Team(Model):
    collection = db.teams
    api_function = api.team
    api_id_name = 'te'
