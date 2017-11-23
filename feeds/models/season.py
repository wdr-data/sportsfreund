from .. import api
from lib.mongodb import db
from .model import Model


class Season(Model):
    collection = db.seasons
    api_function = api.season
    api_id_name = 'se'
