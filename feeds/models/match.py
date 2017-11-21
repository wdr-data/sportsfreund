from .. import api
from lib.mongodb import client as mongo
from .model import Model

db = mongo.main
matches = db.match


class Match(Model):

    @classmethod
    def by_id(cls, id):
        cached = matches.find_one({'id': id})
        if cached:
            return cls(**cached)

        else:
            match = api.match(ma=id)
            new_id = matches.insert_one(match)
            match['_id'] = new_id
            return cls(**match)

