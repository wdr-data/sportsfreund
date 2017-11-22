from .. import api
from lib.mongodb import client as mongo
from .model import Model

db = mongo.main


class Competition(Model):
    collection = db.competitions
    api_function = api.competition
    api_id_name = 'co'
