from enum import Enum
from datetime import datetime

from pymongo import ASCENDING, DESCENDING

from lib.mongodb import db
from .model import ListFeedModel
from .. import api


FEED_PARAMS = {
    548: {'df': '2014-02-07-00-00', 'dt': '2014-02-23-00-00'},  # Sotchi
    1757: {'df': '2018-02-09-00-00', 'dt': '2018-02-26-00-00'},  # PyeongChang
}


class Medal(ListFeedModel):
    collection = db.medals
    api_id_name = 'to'
    cache_time = 60 * 4

    @classmethod
    def api_function(cls, **kwargs):
        kwargs['df'] = FEED_PARAMS[int(kwargs[cls.api_id_name])]['df']
        kwargs['dt'] = FEED_PARAMS[int(kwargs[cls.api_id_name])]['dt']
        return api.medals(**kwargs)

    def __init__(self, *args, **kwargs):
        """
        Medal model. Do not create instances using this constructor, only use the
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

                    se['sport_id'] = sp['id']
                    se['sport'] = sp['name']
                    se['discipline_short'] = (co['shortname']
                                              if co['shortname'] not in {'Olympia'}
                                              else None)
                    se['competition_type'] = co['type']
                    se['gender'] = co['gender']
                    se['start_date'] = datetime.strptime(se['start'], '%Y-%m-%d')
                    se['end_date'] = datetime.strptime(se['end'], '%Y-%m-%d')

                    se['topic_id'] = topic_id
                    se['_cached_at'] = now

                    cls.collection.replace_one({'id': se['id']}, se, upsert=True)

    @classmethod
    def _search(cls, base_filter, sport, discipline, gender, country, sorting=[]):

        try:
            for p in FEED_PARAMS:
                cls.load_feed(p)
        except:
            pass

        filter = {}
        filter['id'] = {'$exists': True}
        filter.update(base_filter)

        if sport is not None:
            filter['sport'] = sport

        if discipline is not None:
            filter['discipline_short'] = discipline

        if gender is not None:
            filter['gender'] = gender

        if country is not None:
            filter['ranking.team.country.name'] = country

        return cls.collection.find(filter).sort(
            sorting +
            [
                ('sport', ASCENDING),
                ('discipline_short', ASCENDING),
            ]
        )

    @classmethod
    def search_last(cls, *, sport=None, discipline=None, gender=None, country=None):
        """
        Searches the last match and returns details about it

        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :param gender: Filter by gender (eg: male, female, mixed)
        :param country: Filter by country
        :return: A `Medal` object of the corresponding match, or `None` if no match was found
        """

        cursor = cls._search(
            {}, sport, discipline, gender, country, sorting=[('end_date', DESCENDING),
                                                             ("_cached_at", DESCENDING)]).limit(1)

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
        :return: A list of `Medal` objects
        """

        filter = {
            'end_date': datetime(date.year, date.month, date.day)
        }

        cursor = cls._search(filter, sport, discipline, gender, country)

        return [cls(**result) for result in cursor]

    @classmethod
    def search_range(cls, *, from_date=None, until_date=None, sport=None, discipline=None,
                     gender=None, country=None):
        """
        Searches for matches on a specific day and returns details about them

        :param from_date: A `datetime.date` object specifying the first date to search
        :param until_date: A `datetime.date` object specifing the last date to search
        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :param gender: Filter by gender (eg: male, female, mixed)
        :param country: Filter by country
        :return: A list of `Medal` objects
        """

        filter = {
            'end_date': {},
        }

        if from_date:
            if not isinstance(from_date, datetime):
                from_date = datetime(from_date.year, from_date.month, from_date.day)
            filter['end_date']['$gte'] = from_date

        if until_date:
            if not isinstance(until_date, datetime):
                until_date = datetime(until_date.year, until_date.month, until_date.day,
                                      hour=23, minute=59, second=59)
            filter['end_date']['$lte'] = until_date

        cursor = cls._search(
            filter, sport, discipline, gender, country, sorting=[('end_date', ASCENDING)])

        return [cls(**result) for result in cursor]

    @classmethod
    def by_country(cls, country, topic_id=None):
        """
        This function will give back all medal winners from a country

        :param country:
        :param topic_id:
        :return:
        """

        if not topic_id:
            topic_id = '1757'

        if topic_id == '548':
            from_date = datetime.strptime('2014-02-01', '%Y-%m-%d').date()
            until_date = datetime.strptime('2014-03-01', '%Y-%m-%d').date()
        elif topic_id == '1757':
            from_date = datetime.strptime('2018-02-01', '%Y-%m-%d').date()
            until_date = None
        else:
            from_date = None
            until_date = None

        all_medal_sets = cls.search_range(from_date=from_date, until_date=until_date, country=country)

        winner_by_country = []
        for medal_set in all_medal_sets:
            for person in medal_set.ranking:
                if person.team.country.name == country:
                    info = {
                        'name': person.team.name,
                        'country': person.team.country,
                        'rank': person.rank,
                        'sport': medal_set.sport,
                        'discipline': medal_set.discipline_short,
                        'gender': medal_set.gender
                    }
                    winner_by_country.append(info)

        return winner_by_country
