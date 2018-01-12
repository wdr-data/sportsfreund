from pymongo import ReturnDocument

from lib.model import Model
from lib.mongodb import db


class UserSentTracking(Model):
    collection = db.user_sent

    @classmethod
    def inc_queued(cls, uid):
        return cls(cls.collection.find_one_and_update(
            {'uid': uid},
            {'$inc': {'last_queued': 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )).last_queued

    @classmethod
    def set_sent(cls, uid, sent_id):
        cls.collection.update(
            {'uid': uid},
            {'$set': {'last_sent': sent_id}},
            upsert=True,
        )

    @classmethod
    def by_id(cls, uid):
        return cls(cls.collection.find_one({'uid': uid}))
