from enum import Enum
from datetime import datetime

from lib.mongodb import db
from .model import ListFeedModel
from .. import api
from feeds.config import sport_by_name


FEED_PARAMS = {
    548: {'df': '2014-02-07-00-00', 'dt': '2014-02-23-00-00'},  # Sotchi
    1757: {'df': '2018-02-09-00-00', 'dt': '2018-02-26-00-00'},  # PyeongChang
}

class Medal(ListFeedModel):
    collection = db.medals
    api_id_name = 'to'

    class Event(Enum):
        OLYMPIA_18 = 'owg18'

    @classmethod
    def api_function(cls, **kwargs):
        kwargs['df'] = FEED_PARAMS[kwargs[cls.api_id_name]]['df']
        kwargs['dt'] = FEED_PARAMS[kwargs[cls.api_id_name]]['dt']
        return api.medals(**kwargs)


    def __init__(self, *args, **kwargs):
        """
        Match metadata model. Do not create instances using this constructor, only use the
        provided factory methods.

        @DynamicAttrs
        """
        super().__init__(*args, **kwargs)

    @property
    def gender_name(self):
        return 'Herren' if self.gender == 'male' else \
            ('Damen' if self.gender == 'female' else 'Mixed')

    @classmethod
    def transform(cls, obj, topic_id, now):
        for sp in obj:
            for co in sp['competition']:
                for se in co['season']:
                    for ra in se['ranking']:
                        ra['item'] = int(ra['item'])
                        ra['rank'] = int(ra['rank'])
                        ra['sport_id'] = sp['id']
                        ra['sport'] = sp['name']
                        ra['discipline_short'] = (co['shortname']
                                                  if co['shortname'] not in {'Olympia'}
                                                  else None)
                        ra['competition_type'] = co['type']
                        ra['gender'] = co['gender']
                        ra['start_date'] = datetime.strptime(se['start'], '%Y-%m-%d')
                        ra['end_date'] = datetime.strptime(se['end'], '%Y-%m-%d')
                        ra['_cached_at'] = now

                        cls.collection.replace_one({'id': ra['id']}, ra, upsert=True)


    @classmethod
    def _search(cls, base_filter, sport, discipline, gender, country):

        try:
            for p in FEED_PARAMS:
                cls.load_feed(p)
        except:
            pass

        filter = base_filter.copy()

        if sport is not None:
            filter['sport'] = sport

        if discipline is not None:
            filter['discipline_short'] = discipline

        if gender is not None:
            filter['gender'] = gender

        if country is not None:
            filter['team.country.name'] = country

        return cls.collection.find(filter)

    @classmethod
    def search_last(cls, *, sport=None, discipline=None, gender=None, country=None):
        """
        Searches the last match and returns details about it

        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :param gender: Filter by gender (eg: male, female, mixed)
        :param country: Filter by country
        :return: A `MatchMeta` object of the corresponding match, or `None` if no match was found
        """

        cursor = cls._search(
            {}, sport, discipline, gender, country).sort([("_cached_at", -1)]).limit(1)

        if cursor and cursor.count():
            result = cursor.next()
            cursor.close()
            return cls(**result)

    @classmethod
    def search_date(cls, date, *, sport=None, discipline=None, gender=None, country=None):
        """
        Searches for matches on a specific day and returns details about them

        :param date: A `datetime.date` object specifying the date on which to search
        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :param gender: Filter by gender (eg: male, female, mixed)
        :param country: Filter by country
        :return: A list of `MatchMeta` objects
        """

        filter = {
            'end_date': datetime(date.year, date.month, date.day)
        }

        cursor = cls._search(filter, sport, discipline, gender, country).sort([("datetime", 1)])

        return [cls(**result) for result in cursor]
