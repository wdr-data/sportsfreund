from datetime import datetime

from .. import api
from lib.mongodb import db
from .model import Model


class Match(Model):
    collection = db.matches
    api_function = api.match
    api_id_name = 'ma'

    @classmethod
    def transform(cls, match):
        """Make the inner 'match' object the new outer object and move 'match_result_at' in it"""

        match['match']['match_result_at'] = match['match_result_at']
        match['datetime'] = datetime.strptime(
            '%s %s' % (match['match_date'], match['match_time']),
            '%Y-%m-%d %H:%M')
        return match['match']
