import requests
import os

from lib.model import Model
from lib.mongodb import db

class Weather(Model):
    """
    Open Weather Map Api model
    """

    collection = db.weather
    cache_time = 600

    feed_url = os.environ.get('VIDEO_FEED_URL')
    @classmethod
    def by_city(cls, city: str, clear_cache: bool=False):
        """
        Get the current weather from open weather map

        :param city: geo-city
        :param clear_cache: If `True`` the feed is reloaded before. Default is false
        :return: current weather
        """

        cls.load_feed({'city': city}, clear_cache=clear_cache)
        obj = cls.collection.find_one({'city': city})

        return cls(**obj)

    @classmethod
    def load_feed(cls, place: dict, cleach_cache: bool=False):
        """

        :param cleach_cache:
        :param place: dictionary given a geocity OR lat and lan
        :return:
        """

        cls.logger.info(f'current weather update')

        cache_marker = cls.collection.find_one({'_cache_marker': True})

        if cache_marker:

            if clear_cache:
                cls.logger.debug('Force-clear video cache')

            elif cache_marker['_cached_at'] + cls.cache_time < time():
                cls.logger.debug('Cache expired')

            else:
                return False

        now = time()

        feed_url = os.environ.get('WEATHER_URL_BASE')
        if not feed_url:
            raise EnvironmentError("Weather Feed URL is not configured!")

        #build ULR

        r = requests.get(feed_url)