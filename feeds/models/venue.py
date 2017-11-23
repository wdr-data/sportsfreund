from .. import api
from lib.mongodb import db
from .model import Model


class Venue(Model):
    collection = db.venues
    api_function = api.venue
    api_id_name = 've'
