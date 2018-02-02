import logging
from os import environ

from django.core.validators import URLValidator

from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from .. import api
from lib.mongodb import db
from .model import FeedModel

logger = logging.getLogger(__name__)


class Person(FeedModel):
    collection = db.persons
    api_function = api.person
    api_id_name = 'pe'
    cache_time = 60 * 60 * 24 * 7

    @classmethod
    def by_id(cls, id, topic_id, additional_data=None, clear_cache=False):
        return super(Person, cls).by_id(id, clear_cache, {'to': topic_id}, additional_data)

    @classmethod
    def get_picture_url(cls, id, topic_id=None):
        if topic_id is not None:
            person = cls.by_id(id, topic_id)
        else:
            person = cls.collection.find_one({'id': str(id)})
        if not person:
            return None

        url = f"{environ.get('PERSON_PICTURE_URL_BASE')}/l/{person['id']}.jpg"
        return url

    @classmethod
    def transform(cls, person):
        sport = person['sport']
        person = person['person']
        person['sport'] = sport

        return person

    @classmethod
    def count_in_feed(cls):
        persons_full = set()
        meta_matches = MatchMeta._search()
        for meta_match in meta_matches:
            try:
                meta_match = MatchMeta(**meta_match)
                if meta_match.get('id') is not None:
                    logger.debug(f"Fetching match {meta_match.id}")
                    match = Match.by_id(meta_match.id)

                    if match.get('match_result') is None:
                        continue

                    for result in match.match_result:
                        if result.get('person') is None:
                            continue

                        persons = result.person

                        if not isinstance(persons, list):
                            persons = [persons]

                        for person in persons:
                            persons_full.add(person.id)
                    print(len(persons_full))
            except Exception as err:
                logger.debug(err)
                continue

        return len(persons_full)
