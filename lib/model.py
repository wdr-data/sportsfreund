import logging
from datetime import time
from enum import Enum


class DotDictList(list):
    def __getitem__(self, key):
        item = super().__getitem__(key)

        if type(item) is dict:
            return DotDict(item)

        elif type(item) is list:
            return DotDictList(item)

        else:
            return item

    def __iter__(self):
        for item in super().__iter__():
            if type(item) is dict:
                yield DotDict(item)

            elif type(item) is list:
                yield DotDictList(item)

            else:
                yield item

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))


class DotDict(dict):
    def __getattr__(self, name):
        item = self[name]

        if type(item) is dict:
            return DotDict(item)

        elif type(item) is list:
            return DotDictList(item)

        else:
            return item

    def __setattr__(self, key, value):
        self[key] = value


class Model(DotDict):

    collection = None

    logger = logging.Logger(__name__)

    @classmethod
    def query(cls, **kwargs):
        """
        Get a list of all model instances from database that fit the filter.
        `kwargs` is used as the filter dict for `find`.
        """
        kwargs = {
            k: v.value if isinstance(v, Enum) else v
            for k, v in kwargs.items()
        }

        return [cls(obj) for obj in cls.collection.find(kwargs)]

    @classmethod
    def delete(cls, **kwargs):
        """
        Delete all model instances from database that fit the filter.
        `kwargs` is used as the filter dict for `delete_many`.

        :return: pymongo.results.DeleteResult
        """

        return cls.collection.delete_many(kwargs)


class CachedListModel(Model):

    cache_time = 0

    @classmethod
    def check_cache_expired(cls):
        cache_marker = cls.collection.find_one({'_cache_marker': True})
        return not cache_marker or cache_marker['_cached_at'] + cls.cache_time < time()
