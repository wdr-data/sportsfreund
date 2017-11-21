import os
import json
from posixpath import join as urljoin
import logging

import requests

logger = logging.Logger(__file__)

FEED_URL_BASE = os.environ.get('FEED_URL')


def api_request(feed, params):
    """
    Make an API request to the data feeds
    :param feed: feed name
    :param params: dict param name: value
    :return: decoded JSON response
    :raises: ValueError if feed failed to load
    """

    feed_portion = urljoin(
        feed,
        *[k + str(v) for k, v in sorted(params.items())])

    logging.info('API REQUEST: %s', feed_portion or '')

    url = urljoin(FEED_URL_BASE, feed_portion)

    r = requests.get(url)

    if r.status_code == 200 and r.content:
        return json.loads(r.content.decode())
    elif r.status_code == 200:
        raise ValueError('Feed %s is empty')
    else:
        raise ValueError('Feed %s failed to load with status code %s'
                         % (feed_portion, r.status_code))


def topic_by_topic(**kwargs):
    """

    :param to: Topic ID
    :return:
    """
    return api_request('topic-by-topic', kwargs)


def match(**kwargs):
    """

    :param ma: Match ID
    :return:
    """
    return api_request('match', kwargs)
