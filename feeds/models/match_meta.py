from time import time as time_
from datetime import datetime, date, time

from .. import api
from lib.mongodb import db
from .model import Model
from .disciplines_alias import DISCIPLINE_ALIASES


class MatchMeta(Model):
    collection = db.matches_meta
    api_function = api.matches_by_topic_for_season
    api_id_name = 'to'

    OLYMPIA = 1757

    SKI_ALPIN = 1773
    BIATHLON = 1814

    TOPIC_IDS = {
        'Ski Alpin': SKI_ALPIN,
        'Biathlon': BIATHLON,
    }

    def __init__(self, **kwargs):
        """
        Match metadata model. Do not create instances using this constructor, only use the
        provided factory methods.

        @DynamicAttrs
        """
        super().__init__(**kwargs)

    @classmethod
    def transform(cls, match):
        """Make the inner 'match' object the new outer object and move 'match_result_at' in it"""

        match['match']['match_result_at'] = match['match_result_at']
        return match['match']

    @classmethod
    def by_id(cls, id, clear_cache=False):
        raise NotImplementedError

    @classmethod
    def load_feed(cls, id, clear_cache=False):
        """
        Load all items in a matches-by-topic-for-season feed if its cache is expired

        :param id: The topic ID
        :param clear_cache: If `True`, the cache for the feed is cleared and it is reloaded
            and cached from the feed. Default is `False`

        :returns `True` if the feed has been updated, else `False` (cache hit)
        """
        id = str(id)

        cls.logger.info('%s match metas in db', cls.collection.count())

        cache_marker = cls.collection.find_one({'_feed_id': id})

        if cache_marker:
            cls.logger.debug('Cache hit for %s with id %s', cls.__name__, id)

            if clear_cache:
                cls.logger.debug('Force-clear cache for %s with id %s', cls.__name__, id)

            elif cache_marker['_cached_at'] + cls.cache_time < time():
                cls.logger.debug('Cache expired for %s with id %s', cls.__name__, id)

            else:
                return False

        obj = cls.api_function(**{cls.api_id_name: id})

        # Single-element list at top level
        sp = obj[0]  # sport object
        now = int(time_())

        for co in sp['competition']:
            for se in co['season']:
                for ro in se['round']:
                    for ma in ro['match']:
                        ma['sport'] = sp['name']
                        ma['sport_id'] = sp['id']
                        ma['season'] = se['name']
                        ma['season_id'] = se['id']
                        ma['competition'] = co['name']
                        ma['competition_id'] = co['id']
                        ma['gender'] = co['gender']
                        ma['discipline'] = ro['name']
                        ma['discipline_short'] = DISCIPLINE_ALIASES.get(ro['name'], ro['name'])
                        ma['_cached_at'] = now
                        ma['datetime'] = datetime.strptime(
                            '%s %s' % (ma['match_date'], ma['match_time']),
                            '%Y-%m-%d %H:%M'
                        )

                        ma['date'] = date.strftime(ma['match_date'], '%Y-%m-%d')
                        ma['time'] = time.strftime(ma['match_time'], '%H:%M')
                        cls.collection.replace_one({'id': ma['id']}, ma, upsert=True)

        cls.logger.info('%s match metas in db', cls.collection.count())

        new_cache_marker = {'_feed_id': id, '_cached_at': now}

        if cache_marker:
            cls.collection.replace_one({'_id': cache_marker['_id']}, new_cache_marker)

        else:
            cls.collection.insert_one(new_cache_marker)

        return True

    @classmethod
    def _search(cls, base_filter, sport, discipline):

        if sport is not None:
            id = cls.TOPIC_IDS[sport]
            cls.load_feed(id)
        else:
            cls.logger.warning('TODO check feeds with only discipline')

        filter = base_filter.copy()

        if sport is not None:
            filter['sport'] = sport

        if discipline is not None:
            filter['discipline_short'] = discipline

        return cls.collection.find(filter)

    @classmethod
    def search_last(cls, sport=None, discipline=None):
        """
        Searches the last match and returns details about it

        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :return: A `MatchMeta` object of the corresponding match, or `None` if no match was found
        """

        now = datetime.now()

        filter = {
            'datetime': {'$lte': now},
        }

        cursor = cls._search(filter, sport, discipline).sort([("datetime", -1)]).limit(1)

        if cursor and cursor.count():
            result = cursor.next()
            cursor.close()
            return cls(**result)

    @classmethod
    def search_next(cls, sport=None, discipline=None):
        """
        Searches the next match and returns details about it

        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :return: A `MatchMeta` object of the corresponding match, or `None` if no match was found
        """

        now = datetime.now()

        filter = {
            'datetime': {'$gte': now},
        }

        cursor = cls._search(filter, sport, discipline).sort([("datetime", 1)]).limit(1)

        if cursor and cursor.count():
            result = cursor.next()
            cursor.close()
            return cls(**result)

    @classmethod
    def search_date(cls, date, sport=None, discipline=None):
        """
        Searches for matches on a specific day and returns details about them

        :param date: A `datetime.date` object specifying the date on which to search
        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :return: A list of `MatchMeta` objects
        """

        filter = {
            'date': date,
        }

        cursor = cls._search(filter, sport, discipline).sort([("datetime", 1)])

        return [cls(**result) for result in cursor]
