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

    logger.info('API REQUEST: %s', feed_portion or '')

    url = urljoin(FEED_URL_BASE, feed_portion)

    r = requests.get(url)

    if r.status_code == 200 and r.content:
        result = json.loads(r.content.decode())

        # empty dict
        if not result:
            raise ValueError('Feed %s is empty' % feed_portion)

        return result

    elif r.status_code == 200:
        raise ValueError('Feed %s is empty' % feed_portion)
    else:
        raise ValueError('Feed %s failed to load with status code %s'
                         % (feed_portion, r.status_code))


def topic_by_topic(**kwargs):
    """

    :param to: Topic ID
    :return:
    """
    return api_request('topic-by-topic', kwargs)


def matches_by_topic_for_season(**kwargs):
    """

    :param to: Topic ID
    :return:
    """
    return api_request('matches-by-topic-for-season', kwargs)


def medals(**kwargs):
    """

    :param to: Topic ID
    :return:
    """
    return api_request('medals', kwargs)


def medals_table(**kwargs):
    """

    :param to: Topic ID
    :return:
    """
    return api_request('medals-table', kwargs)


def match(**kwargs):
    """

    :param ma: Match ID
    :return:
    """
    return api_request('match', kwargs)


def team(**kwargs):
    """

    :param te: Team ID
    :return:
    """
    return api_request('team', kwargs)


def season(**kwargs):
    """

    :param se: Season ID
    :return:
    """
    return api_request('season', kwargs)


def competition(**kwargs):
    """

    :param co: Team ID
    :return:
    """
    return api_request('competition', kwargs)


def sport(**kwargs):
    """

    :param sp: Sport ID
    :return:
    """
    return api_request('sport', kwargs)


def topic(**kwargs):
    """

    :param to: Topic ID
    :return:
    """
    return api_request('topic', kwargs)


def venue(**kwargs):
    """

    :param ve: Venue ID
    :return:
    """
    return api_request('venue', kwargs)
