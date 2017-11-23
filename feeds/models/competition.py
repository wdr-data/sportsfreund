from .. import api
from lib.mongodb import db
from .model import Model


class Competition(Model):
    collection = db.competitions
    api_function = api.competition
    api_id_name = 'co'
