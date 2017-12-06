import logging
from enum import Enum


class Model(dict):

    collection = None

    logger = logging.Logger(__name__)

    def __getattr__(self, name):
        item = self[name]

        if type(item) is dict:
            return Model(item)

        else:
            return item

    def __setattr__(self, key, value):
        self[key] = value

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