from datetime import date, timedelta, datetime

import os

import pytz
import requests
from bs4 import BeautifulSoup
import iso8601

from lib.model import CachedListModel
from lib.mongodb import db

FIELDS = ['sport-id', 'sport-name', 'title', 'moderator', 'event-start', 'event-end', 'channel', 'start', 'end', 'copy']


class Livestream(CachedListModel):

    collection = db.livestreams
    cache_time = 60 * 60  # 1 Hour

    @classmethod
    def next_events(cls):
        cls.load_feed()
        now = datetime.now()
        limit = now + timedelta(days=1)
        return cls.query(start={'$gte': now, '$lt': limit})

    @classmethod
    def load_feed(cls, clear_cache: bool=False, history: int=0):
        if not (clear_cache or cls.check_cache_expired()):
            return

        url_base = os.environ.get('LIVESTREAM_FEED_BASE')
        if url_base is None:
            return

        for delta in range(3 + history):
            day = date.today() + timedelta(days=delta) - timedelta(days=history)
            url = f"{url_base}/{day.strftime('%Y-%m-%d')}.xml"
            r = requests.get(url)
            if r.status_code != 200 or not r.content:
                continue

            feed = BeautifulSoup(r.content.decode(), 'lxml').find('export')
            if not feed:
                continue

            for video in feed.find_all('video', recursive=False):
                if 'ecms-id' in video.attrs:
                    obj = {key: video.find(key, recursive=False).string
                           for key in FIELDS if video.find(key, recursive=False)}
                    for key in ['event-start', 'event-end', 'start', 'end']:
                        obj[key] = iso8601.parse_date(obj[key]).astimezone(pytz.utc)
                    obj['id'] = video['ecms-id']
                    cls.collection.replace_one({'id': obj['id']}, obj, upsert=True)
