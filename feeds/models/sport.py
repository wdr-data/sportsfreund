from .. import api
from lib.mongodb import client as mongo
from .model import Model

db = mongo.main


class Sport(Model):
    collection = db.sports
    api_function = api.sport
    api_id_name = 'sp'
