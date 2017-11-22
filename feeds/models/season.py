from .. import api
from lib.mongodb import client as mongo
from .model import Model

db = mongo.main


class Season(Model):
    collection = db.seasons
    api_function = api.season
    api_id_name = 'se'
