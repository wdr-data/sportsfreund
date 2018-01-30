from abc import abstractmethod, ABCMeta
from time import time as time

from lib.model import Model


class FeedModelList(list):
    def __getitem__(self, key):
        item = super().__getitem__(key)

        if type(item) is dict:
            return FeedModel(item)

        elif type(item) is list:
            return FeedModelList(item)

        else:
            return item

    def __iter__(self):
        for item in super().__iter__():
            if type(item) is dict:
                yield FeedModel(item)

            elif type(item) is list:
                yield FeedModelList(item)

            else:
                yield item

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))


class FeedModel(Model):
    """
    @DynamicAttrs
    """

    api_function = None
    api_id_name = None
    transform = None
    # cache_time = 60 * 60 * 24  # 1d cache by default
    cache_time = 60  # 1m cache for testing

    @classmethod
    def by_id(cls, id, clear_cache=False):
        """
        Get the Model instance by id. If it is found in the cache, it is returned from there.
        Else, a request to the feed is made, the transformation (if defined) is applied, the
        instance is cached and then returned.

        :param id: The id (as specified by the feed) of the instance
        :param clear_cache: If `True`, the cache for the instance is cleared and it is reloaded
            and cached from the feed. Default is `False`
        """
        id = str(id)

        cached = cls.collection.find_one({'id': id})

        if cached:
            cls.logger.debug('Cache hit for %s with id %s', cls.__name__, id)

            if clear_cache:
                cls.logger.debug('Force-clear cache for %s with id %s', cls.__name__, id)

            elif cached['_cached_at'] + cls.cache_time < time():
                cls.logger.debug('Cache expired for %s with id %s', cls.__name__, id)

            else:
                return cls(**cached)

        obj = cls.api_function(**{cls.api_id_name: id})

        if cls.transform:
            obj = cls.transform(obj)

        obj['_cached_at'] = int(time())

        if cached:
            cls.collection.replace_one({'_id': cached['_id']}, obj)
            obj['_id'] = cached['_id']

        else:
            new_id = cls.collection.insert_one(obj)
            obj['_id'] = new_id

        return cls(**obj)

    def __getattr__(self, name):
        item = self[name]

        if type(item) is dict:
            return FeedModel(item)

        elif type(item) is list:
            return FeedModelList(item)

        else:
            return item


class ListFeedModel(FeedModel, metaclass=ABCMeta):
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

        cls.logger.info('%s %s in db', cls.collection.count(), cls.__name__)

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

        cls.transform(obj, id, now)

        cls.logger.info('%s match metas in db', cls.collection.count())

        new_cache_marker = {'_feed_id': id, '_cached_at': now}

        if cache_marker:
            cls.collection.replace_one({'_id': cache_marker['_id']}, new_cache_marker)

        else:
            cls.collection.insert_one(new_cache_marker)

        return True

    @classmethod
    @abstractmethod
    def transform(cls, obj, topic_id, now):
        pass
