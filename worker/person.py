from requests.exceptions import RequestException

from feeds.models.match_meta import MatchMeta
from feeds.models.match import Match
from feeds.models.person import Person


def load_persons():
    meta_matches = MatchMeta._search()
    for meta_match in meta_matches:
        try:
            meta_match = MatchMeta(**meta_match)
            if meta_match.get('id') is not None:
                # Skip deleted matches
                try:
                    match = Match.by_id(meta_match.id)
                except ValueError:
                    continue

                topic_id = meta_match.topic_id

                if match.get('match_result') is None:
                    continue

                for result in match.match_result:
                    if result.get('person') is None:
                        continue

                    persons = result.person

                    if not isinstance(persons, list):
                        persons = [persons]

                    additional_data = {}
                    if result.get('team') is not None:
                        additional_data['team_id'] = result.team.id
                    [Person.by_id(person.id, topic_id, additional_data) for person in persons]
        except Exception as err:
            print(f"Load match {meta_match.get('id')} failed: {str(err)}")
