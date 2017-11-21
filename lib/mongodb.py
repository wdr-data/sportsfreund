import os
from pymongo import MongoClient
client = MongoClient(os.environ.get('MONGODB_URI'))
