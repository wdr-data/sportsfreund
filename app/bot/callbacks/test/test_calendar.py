from datetime import datetime, timedelta
from time import time

from unittest.mock import patch

from pytest import fixture
from mongomock import MongoClient

patch('pymongo.MongoClient', new=MongoClient)

from feeds.models.match_meta import MatchMeta
from ..calendar import api_next
from lib.testing import ExpectedReply, event


@fixture
def collection():
    collection = MongoClient().db.collection

    with patch.object(MatchMeta, 'collection', new=collection), \
         patch.object(MatchMeta, 'load_feed'):
        yield collection


def gen_match(the_date, collection):

    match = {
        'id': '8471341',
        'matchday': '0',
        'match_date': the_date.strftime('%Y-%m-%d'),
        'match_time': the_date.strftime('%H:%M'),
        'finished': 'no',
        'live_status': 'full',
        'venue': {
            'id': '4047',
            'name': 'Gästrappet',
            'town': {'id': '1778', 'name': 'Bremen'},
            'country': {'id': '182', 'name': 'Schweden', 'code': 'SWE', 'iso': 'SE'}
        },
        'sport': 'Biathlon',
        'sport_id': '43',
        'season': '2017/2018',
        'season_id': '24824',
        'competition': 'Weltcup Finale',
        'competition_id': '2068',
        'gender': 'male',
        'discipline': 'Sprint',
        'discipline_short': 'Sprint',
        '_cached_at': int(time()) + 100,
        'match_incident': None,
        'datetime': the_date,
    }

    collection.insert_one(match)

    return match


class TestApiNext:
    def test_future_found(self, event, collection):
        """Finds a single future match according to the query and sends it as a message"""
        the_date = datetime.now() + timedelta(days=1)

        gen_match(the_date, collection)

        parameters = {
            'sport': 'Biathlon',
            'discipline': 'Sprint',
            'town': 'Bremen',
            'date': the_date.strftime('%Y-%m-%d'),
            'date-period': None,
            'country': None,
        }

        api_next(event, parameters)

        timestr = the_date.strftime('%A, %d.%m.%Y um %H:%M')

        ExpectedReply(event).expect_text(
            'Gucken wir mal was da so los sein wird.'
        ).expect_text(
            f'Am {timestr} Uhr: Sprint der Herren in Bremen 🇸🇪 SWE'
        )

    def test_future_not_found(self, event, collection):
        gen_match(datetime.now() - timedelta(days=1), collection)

        the_date = datetime.now() + timedelta(days=1)

        parameters = {
            'sport': 'Biathlon',
            'discipline': 'Sprint',
            'town': 'Bremen',
            'date': the_date.strftime('%Y-%m-%d'),
            'date-period': None,
            'country': None,
        }

        api_next(event, parameters)

        ExpectedReply(event).expect_text(
            'Gucken wir mal was da so los sein wird.'
        ).expect_text(
            [f'Heute findet kein Wintersport-Event statt. Ich geh ne Runde {emoji}!'
             for emoji in ('⛷', '🏂')]
        )
