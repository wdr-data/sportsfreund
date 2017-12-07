from datetime import datetime, timedelta
from typing import Iterable, List

from itertools import islice

from feeds.models.match_meta import MatchMeta
from feeds.models.team import Team
from lib.flag import flag
from lib.response import list_element, button_postback
from .. import api
from lib.mongodb import db
from .model import FeedModel


class Match(FeedModel):
    collection = db.matches
    api_function = api.match
    api_id_name = 'ma'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._meta = None
        self._winner_result = None

    @classmethod
    def transform(cls, match):
        """Make the inner 'match' object the new outer object and move 'match_result_at' in it"""

        match['match']['match_result_at'] = match['match_result_at']
        match = match['match']
        match['finished'] = match['finished'] == 'yes'
        match['datetime'] = datetime.strptime(
            '%s %s' % (match['match_date'], match['match_time']),
            '%Y-%m-%d %H:%M')
        for mr in match['match_result']:
            mr['rank'] = int(mr['rank'])
            mr['match_result'] = int(mr['match_result'])
        return match

    def results_by_country(self, country: str) -> Iterable[FeedModel]:
        """
        Filter end results of this match by country
        :param country: Full name of the country
        :returns:
        """

        yield from (r for r in self.results if Team.by_id(r.team_id).country.name == country)

    def results_by_team(self, team: str) -> Iterable[FeedModel]:
        """
        Filter end results of this match by team
        :param team: Full name of the team
        :returns:
        """

        yield from (r for r in self.results if Team.by_id(r.team_id).name == team)

    @property
    def results(self) -> List[FeedModel]:
        """
        Returns ordered end results
        :return:
        """
        return sorted(
            (r for r in self.match_result if r.match_result_at == '0'),
            key=(lambda r: int(r.rank)))

    @property
    def meta(self):
        if not self._meta:
            self._meta = MatchMeta.by_match_id(self.id)
        return self._meta

    @property
    def winner_result(self):
        if not self._winner_result:
            self._winner_result = self.results[0]
        return self._winner_result

    @property
    def lst_podium(self):
        winner_results = self.results[:3]
        winner_teams = [Team.by_id(winner.team_id) for winner in winner_results]

        for r in winner_results:
            r.match_result = int(r.match_result)

        winning_points = winner_results[0].match_result

        header = [list_element(
            self.venue.name,
            f'{self.meta.sport}, {self.meta.discipline}',
            image_url='https://i.imgur.com/DnWwUM5.jpg' if self.meta.sport == 'Ski Alpin'
            else 'https://i.imgur.com/Bu05xF6.jpg'
        )]

        for i, (winner_team, winner_result) in enumerate(zip(winner_teams, winner_results)):
            header.append(
                list_element(
                    f'{Match.medal(i + 1)} {winner_team.name}, {flag(winner_team.country.iso)}',
                    f'{self.txt_points(winner_result)}',
                    image_url=Match.medal_pic(i + 1)))

        return header

    def txt_points(self, result):
        if result.rank == 1:
            point_str = result.match_result
        else:
            point_str = result.match_result - self.winner_result.match_result

        if self.meta.sport in ['Biathlon']:
            point_str = Match.fmt_millis(point_str, digits=1)
        elif self.meta.sport in ['Ski Alpin']:
            point_str = Match.fmt_millis(point_str, digits=2)

        if result.rank != 1:
            point_str = '+' + point_str

        return point_str

    @property
    def btn_podium(self):
        return button_postback('Mehr Platzierungen', {'result_details': self.id})

    @property
    def txt_podium(self):
        winner_results = self.results[:3]
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

    @staticmethod
    def medal_pic(rank):
        medals = {
            1: 'https://i.imgur.com/U48Nd50.png',
            2: 'https://i.imgur.com/GEo7KP8.png',
            3: 'https://i.imgur.com/ySPUnRT.png'
        }
        return medals[rank]

    @staticmethod
    def fmt_millis(t: str, digits: int = 2) -> str:
        dt, micro = (datetime(1970, 1, 1) + timedelta(milliseconds=int(t))).strftime(
            '%H:%M:%S.%f').split('.')

        while dt[0] in ('0', ':') and len(dt) > 1:
            dt = dt[1:]

        return f'{dt}.{int(micro) // 10 ** (6 - digits)}'
