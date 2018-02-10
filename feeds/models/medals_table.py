from pymongo import ASCENDING

from feeds.models.match_meta import MatchMeta
from .. import api
from lib.mongodb import db
from .model import ListFeedModel


class MedalsTable(ListFeedModel):
    collection = db.medals_table
    api_function = api.medals_table
    api_id_name = 'to'
    cache_time = 60 * 5

    def __init__(self, *args, **kwargs):
        """
        Match metadata model. Do not create instances using this constructor, only use the
        provided factory methods.

        @DynamicAttrs
        """
        super().__init__(*args, **kwargs)

    @classmethod
    def transform(cls, obj, topic_id, now):
        for i, co in enumerate(obj, start=1):
            co['first'] = int(co['first'])
            co['second'] = int(co['second'])
            co['third'] = int(co['third'])
            co['rank'] = i
            co['topic_id'] = topic_id
            cls.collection.replace_one({'id': co['id'], 'topic_id': topic_id}, co, upsert=True)

    @classmethod
    def _search(cls, base_filter, country=None, topic_id=None, sorting=[]):

        for id in MatchMeta.olympia_feeds:
            cls.load_feed(id, clear_cache=True)

        filter = {}
        filter['id'] = {'$exists': True}
        filter.update(base_filter)

        if country is not None:
            filter['country.name'] = country

        if topic_id is not None:
            filter['topic_id'] = topic_id
        else:
            filter['topic_id'] = '1757'

        return cls.collection.find(filter).sort(
            sorting +
            [
                ('rank', ASCENDING),
                ('first', ASCENDING),
                ('second', ASCENDING),
                ('third', ASCENDING),
                ('country.name', ASCENDING),
            ]
        )


    @classmethod
    def by_country(cls, *, country=None, topic_id=None):
        """
        Searches the last match and returns details about it

        :param country: Filter by country
        :return: A `MatchMeta` object, or `None` if nothing was found
        """

        cursor = cls._search({}, country=country, topic_id=topic_id).limit(1)

        if cursor and cursor.count():
            result = cursor.next()
            cursor.close()
            return cls(**result)

    @classmethod
    def top(cls, *, number, topic_id=None):
        """
        Searches the last match and returns details about it

        :param country: Integer of members to show
        :return: A `MatchMeta` object, or `None` if nothing was found
        """

        cursor = cls._search({}, topic_id=topic_id).limit(number)

        return [cls(**result) for result in cursor]

    @classmethod
    def with_medals(cls, topic_id=None):
        """
        Searches the all countries with min. one medal and returns details about it

        :return: A list of `MatchMeta` objects, or `None` if nothing was found
        """

        cursor = cls._search({'$or': [{'first': {'$ne': 0}},
                                      {'second': {'$ne': 0}},
                                      {'third': {'$ne': 0}}]}, topic_id=topic_id)

        return [cls(**result) for result in cursor]
