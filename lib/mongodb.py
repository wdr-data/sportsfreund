import os
from pymongo import MongoClient

db = None

try:
    MONGODB_URI = os.environ['MONGODB_URI']
    client = MongoClient(MONGODB_URI)
    db = client.get_database()
except KeyError:
    db = MongoClient().main
