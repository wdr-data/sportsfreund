from time import time
import logging


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


class Model(dict):

    collection = None

    logger = logging.Logger(__name__)

    def __getattr__(self, name):
        item = self[name]

        if type(item) is dict:
            return Model(item)

        else:
            return item

    @classmethod
    def query(cls, **kwargs):
        return [cls(obj) for obj in cls.collection.find(kwargs)]


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
