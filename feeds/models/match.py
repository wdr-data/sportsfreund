from .. import api
from lib.mongodb import client as mongo
from .model import Model

db = mongo.main


class Match(Model):
    collection = db.matches
    api_function = api.match
    api_id_name = 'ma'

    @classmethod
    def transform(cls, match):
        """Make the inner 'match' object the new outer object and move 'match_result_at' in it"""

        match['match']['match_result_at'] = match['match_result_at']
        return match['match']
