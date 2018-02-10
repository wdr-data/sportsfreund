import locale

from pymongo import ASCENDING

from lib.mongodb import db
from .. import api
from .model import ListFeedModel

locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')


class Standing(ListFeedModel):
    collection = db.standings
    api_function = api.standing
    api_id_name = 'se'
    cache_time = 60*5

    season_feeds = [24752, 24753, 24754, 24732, 24733]

    @classmethod
    def transform(cls, obj, id, now):
        round = obj['standing']
        for standing in round:
            standing['season_id'] = id
            cls.collection.replace_one({'team_id': standing['team']['id']}, standing, upsert=True)

    @classmethod
    def load_standings(cls):
        for id in cls.season_feeds:
            cls.load_feed(id)

    @classmethod
    def _search(cls, base_filter, season_id=None, round_name=None):

        try:
            cls.load_standings()
        except:
            pass

        filter = {}
        filter['id'] = {'$exists': True}
        filter.update(base_filter)

        if season_id is not None:
            filter['season_id'] = season_id

        if round_name is not None:
            filter['round.name'] = round_name

        return cls.collection.find(filter).sort(
            [
                ('rank', ASCENDING),
                ('team.name', ASCENDING),
            ]
        )

    @classmethod
    def by_season_round(cls, season_id=None, round_name=None):
        """
        Searches for rounds in a specific season ond/or round

        :param season_id:
        :param round_name:
        :return: A list of `Standing` objects
        """

        cursor = cls._search(base_filter={}, season_id=season_id, round_name=round_name)

        return [cls(**result) for result in cursor]
