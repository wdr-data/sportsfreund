from pymongo import DESCENDING

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
        i=1
        for co in obj:
            co['first'] = int(co['first'])
            co['second'] = int(co['second'])
            co['third'] = int(co['third'])
            co['rank'] = i
            cls.collection.replace_one({'id': co['id']}, co, upsert=True)
            i+=1

    @classmethod
    def _search(cls, base_filter, country=None, sorting=[]):

        try:
            cls.load_feed(548)
        except:
            pass

        filter = {}
        filter['id'] = {'$exists': True}
        filter.update(base_filter)

        if country is not None:
            filter['country.name'] = country

        return cls.collection.find(filter).sort(
            sorting +
            [
                ('first', DESCENDING),
                ('second', DESCENDING),
                ('third', DESCENDING),
                ('country.name', DESCENDING),
            ]
        )

    @classmethod
    def by_country(cls, *, country=None):
        """
        Searches the last match and returns details about it

        :param country: Filter by country
        :return: A `MatchMeta` object, or `None` if nothing was found
        """

        cursor = cls._search({}, country).limit(1)

        if cursor and cursor.count():
            result = cursor.next()
            cursor.close()
            return cls(**result)

    @classmethod
    def top(cls, *, number):
        """
        Searches the last match and returns details about it

        :param country: Integer of members to show
        :return: A `MatchMeta` object, or `None` if nothing was found
        """

        cursor = cls._search({}).limit(number)

        return [cls(**result) for result in cursor]

    @classmethod
    def with_medals(cls):
        """
        Searches the all countries with min. one medal and returns details about it

        :return: A list of `MatchMeta` objects, or `None` if nothing was found
        """

        cursor = cls._search({'$or': [{'first': {'$ne': 0}},
                                      {'second': {'$ne': 0}},
                                      {'third': {'$ne': 0}}]})

        return [cls(**result) for result in cursor]
