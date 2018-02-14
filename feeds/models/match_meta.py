from datetime import datetime, timedelta
from enum import Enum
from time import time as time

from feeds.config import DISCIPLINE_ALIASES, SPORT_BY_NAME, discipline_config, SPORTS_CONFIG
from lib.mongodb import db
from .model import ListFeedModel
from .. import api


class MatchMeta(ListFeedModel):
    collection = db.matches_meta
    api_function = api.matches_by_topic_for_season
    api_id_name = 'to'
    cache_time = 60 * 60 * 24

    olympia_feeds = [1757, 548]

    class Event(Enum):
        OLYMPIA_18 = 'owg18'
        OLYMPIA_14 = 'owg14'
        WORLDCUP = 'worldcup'

    def __init__(self, *args, **kwargs):
        """
        Match metadata model. Do not create instances using this constructor, only use the
        provided factory methods.

        @DynamicAttrs
        """
        super().__init__(*args, **kwargs)
        try:
            self.event = self.Event(self.event)
        except KeyError:
            self.event = None
        except ValueError:
            pass

    def __getattr__(self, item):
        try:
            return super().__getattr__(item)
        except KeyError:
            if item == 'venue':
                return {
                    "id": "9999",
                    "name": "Great Hall",
                    "town": {
                        "id": "4999",
                        "name": "veng wa'DIch",
                    },
                    "country": {
                        "id": "999",
                        "name": "Qo'noS",
                        "code": "TNG",
                        "iso": "🏳️‍🌈",
                    },
                }


    @property
    def town(self):
        return self.venue.town.name

    @property
    def country(self):
        return self.venue.country.name

    @property
    def gender_name(self):
        return 'Herren' if self.gender == 'male' else \
            ('Damen' if self.gender == 'female' else 'Mixed')

    @classmethod
    def by_id(cls, id, clear_cache=False):
        raise NotImplementedError

    @classmethod
    def by_match_id(cls, match_id):
        try:
            return cls.query(id=match_id)[0]
        except IndexError:
            return None

    @classmethod
    def by_round_id(cls, round_id):
        return cls.query(round_id=round_id)

    @classmethod
    def by_season_id(cls, season_id):
        return cls.search_range(season_id=season_id)

    @classmethod
    def transform(cls, obj, topic_id, now):
        # Single-element list at top level
        sp = obj[0]  # sport object
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
                        discipline_clean = ro['name'].split('(')[0].rstrip()
                        ma['discipline_short'] = DISCIPLINE_ALIASES.get(discipline_clean,
                                                                        discipline_clean)
                        ma['_cached_at'] = now
                        ma['match_incident'] = ma.get('match_incident')

                        if ma['match_time'] == 'unknown':
                            ma['match_time'] = 'unbekannt'
                            datetime_str = '%s %s' % (ma['match_date'], '23:59')
                        else:
                            datetime_str = '%s %s' % (ma['match_date'], ma['match_time'])

                        ma['datetime'] = datetime.strptime(
                            datetime_str,
                            '%Y-%m-%d %H:%M'
                        )

                        ma['topic_id'] = topic_id
                        ma['event'] = cls.Event.WORLDCUP.value

                        cls.collection.replace_one({'id': ma['id']}, ma, upsert=True)

    @classmethod
    def load_olympia_feed(cls, id, clear_cache=False):
        """
        Load all items in a matches-by-topic-for-season feed if its cache is expired

        :param id: The topic ID
        :param clear_cache: If `True`, the cache for the feed is cleared and it is reloaded
            and cached from the feed. Default is `False`

        :returns `True` if the feed has been updated, else `False` (cache hit)
        """
        id = str(id)

        cls.logger.info('%s olympic match metas in db', cls.collection.count())

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

        now = int(time())

        for sp in obj:
            if sp['name'] in SPORT_BY_NAME:
                for co in sp['competition']:
                    for se in co['season']:
                        for ro in se['round']:
                            for ma in ro['match']:
                                ma['sport'] = sp['name']
                                ma['sport_id'] = sp['id']
                                ma['season'] = se['name']
                                ma['season_id'] = se['id']
                                ma['competition'] = ro['name']
                                ma['competition_id'] = ro['id']
                                ma['gender'] = co['gender']
                                ma['discipline'] = co['name']
                                if co['shortname'] == 'Olympia':
                                    ma['discipline_short'] = DISCIPLINE_ALIASES.get(ro['name'],
                                                                                    ro['name'])
                                else:
                                    ma['discipline_short'] = DISCIPLINE_ALIASES.get(co['shortname'],
                                                                                co['shortname'])
                                ma['_cached_at'] = now
                                ma['match_incident'] = ma.get('match_incident')

                                ma['round'] = ro['name']

                                config = discipline_config(ma['sport'], ma['discipline_short'])

                                if isinstance(config, dict) and 'rounds' in config:
                                    ma['round_mode'] = ro['name']
                                    ma['round_id'] = ro['id']
                                else:
                                    ma['round_mode'] = None
                                    ma['round_id'] = None

                                if 'match_meta' in ma:
                                    for element in ma['match_meta']:
                                        if 'kind' in element and element['kind'] == 'medals':
                                            ma['medals'] = element['content']
                                else:
                                    ma['medals'] = None

                                if ma['match_time'] == 'unknown':
                                    ma['match_time'] = 'unbekannt'
                                    datetime_str = '%s %s' % (ma['match_date'], '23:59')
                                else:
                                    datetime_str = '%s %s' % (ma['match_date'], ma['match_time'])

                                ma['datetime'] = datetime.strptime(
                                    datetime_str,
                                    '%Y-%m-%d %H:%M'
                                )

                                ma['topic_id'] = id
                                if id == '1757':
                                    ma['event'] = cls.Event.OLYMPIA_18.value
                                else:
                                    ma['event'] = cls.Event.OLYMPIA_14.value

                                cls.collection.replace_one({'id': ma['id']}, ma, upsert=True)

        cls.logger.info('%s match metas in db', cls.collection.count())

        new_cache_marker = {'_feed_id': id, '_cached_at': now}

        if cache_marker:
            cls.collection.replace_one({'_id': cache_marker['_id']}, new_cache_marker)

        else:
            cls.collection.insert_one(new_cache_marker)

        return True

    @classmethod
    def load_all_feeds(cls, sport=None):
        if sport is not None:
            try:
                id = SPORT_BY_NAME[sport].topic_id
                cls.load_feed(id)
            except:
                pass

        else:
            for sport in SPORTS_CONFIG:
                if sport.topic_id is not None:
                    cls.load_feed(sport.topic_id)

        for id in cls.olympia_feeds:
            cls.load_olympia_feed(id)

    @classmethod
    def _search(cls, base_filter=None, sport=None, discipline=None,
                town=None, country=None, gender=None, round_mode=None, event=None,
                 medals=None, season_id=None):

        cls.load_all_feeds(sport)

        filter = {}
        filter['id'] = {'$exists': True}
        if base_filter is not None:
            filter.update(base_filter)

        if sport is not None:
            filter['sport'] = sport

        if discipline is not None:
            filter['discipline_short'] = discipline

        if town is not None:
            filter['venue.town.name'] = town

        if country is not None:
            filter['venue.country.name'] = country

        if gender is not None:
            filter['gender'] = gender

        if round_mode is not None:
            filter['round_mode'] = round_mode

        if event is not None:
            filter['event'] = event

        if season_id is not None:
            filter['season_id'] = season_id

        if medals is not None:
            if medals == 'all':
                filter['medals'] = {'$in': ['complete', 'gold_silver', 'bronze_winner']}
            else:
                filter['medals'] = medals

        return cls.collection.find(filter)

    @classmethod
    def search_last(cls, *, sport=None, discipline=None, town=None,
                    country=None, gender=None, round_mode=None, event=None, medals=None):
        """
        Searches the last match and returns details about it

        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :param town: Filter by the name of the town (eg. "Gangneung")
        :param country: Filter by the name of the country (eg. "Südkorea")
        :param gender: Filter by gender (eg: male, female, mixed)
        :param round_mode: Filter by round_mode (eg: Viertelfinale, Qualifikation, Entscheidung)
        :param event: MatchMeta.Event (OLYMPIA_18, OLYMPIA_14, WORLDCUP)
        :param medals: Filter by Medals ( 'all kinds, 'complete', 'gold_silver', 'bronze_winner')
        :return: A `MatchMeta` object of the corresponding match, or `None` if no match was found
        """

        now = datetime.now()

        filter = {
            'datetime': {'$lte': now},
        }

        cursor = cls._search(
            filter, sport, discipline, town,
            country, gender, round_mode, event, medals).sort([("datetime", -1)]).limit(1)

        if cursor and cursor.count():
            result = cursor.next()
            cursor.close()
            return cls(**result)

    @classmethod
    def search_next(cls, *, sport=None, discipline=None, town=None, country=None,
                    gender=None, round_mode=None, event=None, medals=None):
        """
        Searches the next match and returns details about it

        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :param town: Filter by the name of the town (eg. "Gangneung")
        :param country: Filter by the name of the country (eg. "Südkorea")
        :param gender: Filter by gender (eg: male, female, mixed)
        :param round_mode: Filter by round_mode (eg: Viertelfinale, Qualifikation, Entscheidung)
        :param event: MatchMeta.Event (OLYMPIA_18, OLYMPIA_14, WORLDCUP)
        :param medals: Filter by Medals ( 'all kinds, 'complete', 'gold_silver', 'bronze_winner')
        :return: A `MatchMeta` object of the corresponding match, or `None` if no match was found
        """

        now = datetime.now()

        filter = {
            'datetime': {'$gte': now},
        }

        cursor = cls._search(
            filter, sport, discipline, town,
            country, gender, round_mode, event, medals).sort([("datetime", 1)]).limit(1)

        if cursor and cursor.count():
            result = cursor.next()
            cursor.close()
            return cls(**result)

    @classmethod
    def search_date(cls, date, *, sport=None, discipline=None, town=None,
                    country=None, gender=None, round_mode=None, event=None, medals=None):
        """
        Searches for matches on a specific day and returns details about them

        :param date: A `datetime.date` object specifying the date on which to search
        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :param town: Filter by the name of the town (eg. "Gangneung")
        :param country: Filter by the name of the country (eg. "Südkorea")
        :param gender: Filter by gender (eg: male, female, mixed)
        :param event: MatchMeta.Event (OLYMPIA_18, OLYMPIA_14, WORLDCUP)
        :param medals: Filter by Medals ( 'all kinds, 'complete', 'gold_silver', 'bronze_winner')
        :param round_mode: Filter by round_mode (eg: Viertelfinale, Qualifikation, Entscheidung)
        :return: A list of `MatchMeta` objects
        """

        filter = {
            'match_date': date.isoformat(),
        }

        cursor = cls._search(filter, sport, discipline, town,
                             country, gender, round_mode).sort([("datetime", 1)])

        return [cls(**result) for result in cursor]

    @classmethod
    def search_range(cls, *, from_date=None, until_date=None, sport=None, discipline=None,
                     town=None, country=None, gender=None,
                     round_mode=None, event=None, medals=None, season_id=None):
        """
        Searches for matches on a specific day and returns details about them

        :param from_date: A `datetime.date` or `datetime.datetime` object specifying the earliest
            date to search
        :param until_date: A `datetime.date` or `datetime.datetime` object specifying the latest
            date to search
        :param sport: Filter by the name of the sport (eg. "Ski Alpin")
        :param discipline: Filter by the short-name of the discipline (eg. "Slalom")
        :param town: Filter by the name of the town (eg. "Gangneung")
        :param country: Filter by the name of the country (eg. "Südkorea")
        :param gender: Filter by gender (eg: male, female, mixed)
        :param round_mode: Filter by round_mode (eg: Viertelfinale, Qualifikation, Entscheidung)
        :param event: MatchMeta.Event (OLYMPIA_18, OLYMPIA_14, WORLDCUP)
        :param medals: Filter by Medals ( 'all kinds, 'complete', 'gold_silver', 'bronze_winner')
        :return: A list of `MatchMeta` objects
        """

        filter = {
            'datetime': {}
        }

        if from_date:
            if not isinstance(from_date, datetime):
                from_date = datetime(from_date.year, from_date.month, from_date.day)
            filter['datetime']['$gte'] = from_date

        if until_date:
            if not isinstance(until_date, datetime):
                until_date = datetime(
                    until_date.year, until_date.month, until_date.day) + timedelta(days=1)
            filter['datetime']['$lte'] = until_date

        if not filter['datetime']:
            del filter['datetime']

        cursor = cls._search(filter, sport, discipline,
                             town, country, gender, round_mode,
                             event, medals, season_id).sort([("datetime", 1)])

        return [cls(**result) for result in cursor]
