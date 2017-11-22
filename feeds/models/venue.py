from .. import api
from lib.mongodb import client as mongo
from .model import Model

db = mongo.main


class Venue(Model):
    collection = db.venues
    api_function = api.venue
    api_id_name = 've'
