import json
from typing import TypeVar, List

import m3u8
import pymongo
import re
from time import time
from urllib.parse import urlparse

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from lib.model import Model
from lib.mongodb import db


class Video(Model):
    """
    @DynamicAttrs
    """

    collection = db.videos
    cache_time = 60

    @classmethod
    def by_id(cls, id: str, clear_cache: bool=False):
        """
        Get the Model instance by id. If it is found in the cache, it is returned from there.
        Else, a request to the feed is made, the instance is cached and then returned.

        :param id: The id (as specified by the feed) of the video
        :param clear_cache: If `True`, the feed is reloaded before. Default is `False`
        """
        id = id
        cls.load_feed(clear_cache=clear_cache)
        obj = cls.collection.find_one({'id': id})

        return cls(**obj)

    @classmethod
    def by_keyword(cls,
                   keywords: TypeVar('str or list of str', str, List[str]),
                   limit: int=1,
                   max_duration=240,
                   clear_cache: bool=False,
                   ):
        """
        Case insensitive search ordered by date published, showing latest first.
        Searches for videos that are tagged with all the keywords passed.

        :param keywords: Single keyword or list of keywords
        :param limit: Number of results. Default is ``1``
        :param max_duration: Maximum allowed video duration in seconds
        :param clear_cache: If the feed should be reloaded before the search. Default is ``False``
        :return: Single ``Video`` or None, if ``limit`` is ``1``, else a list of ``Video``
        """
        cls.load_feed(clear_cache=clear_cache)

        if isinstance(keywords, str):
            keywords = keywords.lower().split()
        else:
            keywords = [kw.lower().split() for kw in keywords]
            keywords = [item for sublist in keywords for item in sublist]  # Flatten list

        mapping = {
            'male': 'herren',
            'female': 'damen',
        }

        keywords = [mapping.get(word, word) for word in keywords]

        filter = {
            'keywords': {'$all': keywords},
            'duration': {'$lte': max_duration},
        }

        if not keywords:
            del filter['keywords']

        cur = cls.collection.find(
            filter
        ).sort(
            'published', pymongo.DESCENDING
        ).limit(limit)

        results = list(cur)

        if limit == 1:
            if results:
                return cls(results[0])
            else:
                return None
        else:
            return [cls(r) for r in results]

    @classmethod
    def load_feed(cls, clear_cache: bool=False):
        """
        Load all items in the video feed if its cache is expired

        :param clear_cache: If `True`, the cache for the feed is cleared and it is reloaded
            and cached from the feed. Default is `False`

        :returns `True` if the feed has been updated, else `False` (cache hit)
        """

        cls.logger.info('%s videos in db', cls.collection.count())

        cache_marker = cls.collection.find_one({'_cache_marker': True})

        if cache_marker:

            if clear_cache:
                cls.logger.debug('Force-clear video cache')

            elif cache_marker['_cached_at'] + cls.cache_time < time():
                cls.logger.debug('Cache expired')

            else:
                return False

        now = time()

        feed_url = os.environ.get('VIDEO_FEED_URL')
        if not feed_url:
            raise EnvironmentError("Video Feed URL is not configured!")

        r = requests.get(feed_url)

        if r.status_code == 200 and r.content:
            feed = BeautifulSoup(r.content.decode(), 'xml')

        else:
            raise ValueError('Video feed failed to load with status code %s'
                             % r.status_code)

        for e in feed.find_all('entry'):

            entry_id = e.id.string
            updated = datetime.strptime(e.updated.string, '%Y-%m-%dT%H:%M:%SZ')

            # Load video from db to check if it was updated in feed
            query = cls.query(id=entry_id)  # Don't use by_id to prevent feed update loop

            if query:
                if query[0].updated == updated:
                    continue

            href = e.link['href']

            r = requests.get(href)

            if r.status_code == 200 and r.content:
                page = BeautifulSoup(r.content.decode(), 'lxml')

            else:
                cls.logger.error(f"Video page {href} failed to load with status code "
                                 f"{r.status_code}")
                continue

            try:
                meta_keywords = page.find('meta', attrs={'name': 'Keywords'})
                keywords = [kw.lower().strip() for kw in meta_keywords['content'].split(',')]

                meta_duration = page.find('meta', attrs={'itemprop': 'duration'})
                duration = datetime.strptime(meta_duration['content'], '%H:%M:%S')
                duration = int((
                        duration -
                        datetime(duration.year, duration.month, duration.day)
                ).total_seconds())

            except:
                cls.logger.exception(f'Page {href} failed to parse')
                continue

            try:
                video_url = Video.extract_video_url(page)
                r = requests.head(video_url)

                if r.status_code != 200:
                    cls.logger.error(
                        f'Extracted video URL for {href} returns {r.status_code}, skipping entry.')
                    continue

            except:
                cls.logger.exception(f'Extracting video URL for {href} failed, skipping entry.')
                continue

            cls.collection.replace_one(
                {
                    'id': entry_id
                },
                {
                    'id': entry_id,
                    'title': e.title.string,
                    'summary': e.summary.string,
                    'video_url': video_url,
                    'duration': duration,
                    'keywords': keywords,
                    'published': datetime.strptime(e.published.string, '%Y-%m-%dT%H:%M:%SZ'),
                    'updated': updated,
                }
                , upsert=True)

        cls.logger.info('%s videos in db', cls.collection.count())

        new_cache_marker = {'_cache_marker': True, '_cached_at': now}
        cls.collection.replace_one({'_cache_marker': True}, new_cache_marker, upsert=True)

        return True

    @staticmethod
    def extract_video_url(dom: BeautifulSoup):

        media_url = dom.find("a", {"class": "mediaLink video"})['data-extension']
        meta_url = json.loads(media_url)['mediaObj']['url']
        id = os.path.splitext(os.path.basename(urlparse(meta_url).path))[0]

        short_id = str(id)[:3]

        playlist_base = os.environ['VIDEO_PLAYLISTS_BASE']
        hls_links = requests.get(
            f"{playlist_base}/{short_id}/{id}.js").text
        meta_url_data = json.loads(re.search(r'^[^{}]+({.*})[^{}]+$', hls_links).group(1))
        url = meta_url_data['mediaResource']['dflt']['videoURL']

        hls_stream = requests.get(f"https:{url}").text
        metadata = m3u8.loads(hls_stream)

        sorted_playlist = sorted(metadata.playlists,
                                 key=lambda x: x.stream_info.resolution or (0, 0), reverse=True)

        hls_uri = sorted_playlist[0].uri
        hls_basename = os.path.basename(urlparse(hls_uri).path)
        index = re.search(r'^index_(\d+)_av\.m3u8$', hls_basename).group(1)
        sizes = re.findall(r'\d+_\d+', hls_uri)

        full_id = sizes[int(index)]

        video_url_base = os.environ['VIDEO_URL_BASE']
        final_url = f"{video_url_base}/{short_id}/{id}/{full_id}.mp4"

        return final_url
