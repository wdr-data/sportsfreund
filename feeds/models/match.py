from datetime import datetime
from typing import Iterable

from itertools import islice

from feeds.models.team import Team
from lib.flag import flag
from .. import api
from lib.mongodb import db
from .model import FeedModel


class Match(FeedModel):
    collection = db.matches
    api_function = api.match
    api_id_name = 'ma'

    @classmethod
    def transform(cls, match):
        """Make the inner 'match' object the new outer object and move 'match_result_at' in it"""

        match['match']['match_result_at'] = match['match_result_at']
        match = match['match']
        match['finished'] = match['finished'] == 'yes'
        match['datetime'] = datetime.strptime(
            '%s %s' % (match['match_date'], match['match_time']),
            '%Y-%m-%d %H:%M')
        return match

    def results_by_country(self, country: str) -> Iterable[FeedModel]:
        """
        Filter results of this match by country
        :param country: Full name of the country
        :returns:
        """

        yield from (r for r in self.match_result if Team.by_id(r.team_id).country.name == country)

    def results_by_team(self, team: str) -> Iterable[FeedModel]:
        """
        Filter results of this match by team
        :param team: Full name of the team
        :returns:
        """

        yield from (r for r in self.match_result if Team.by_id(r.team_id).name == team)

    @property
    def txt_podium(self):
        winner_results = islice(sorted((r for r in self.match_result if r.match_result_at == '0'),
                                key=(lambda r: int(r.rank))), 3)
        winner_teams = [Team.by_id(winner.team_id) for winner in winner_results]

        return '\n'.join(
            '{i} {winner}'.format(
                i=Match.medal(i + 1),
                winner=' '.join([winner_team.name,
                                 flag(winner_team.country.iso)]))
            for i, winner_team in enumerate(winner_teams))

    @staticmethod
    def medal(rank):
        medals = {
            1: '🥇',
            2: '🥈',
            3: '🥉'
        }
        return medals[rank]
