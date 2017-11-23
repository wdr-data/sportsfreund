from .. import api
from lib.mongodb import db
from .model import Model


class Sport(Model):
    collection = db.sports
    api_function = api.sport
    api_id_name = 'sp'
