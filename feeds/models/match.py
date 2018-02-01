from datetime import datetime, timedelta
from calendar import day_name
from typing import Iterable, List
import locale

from feeds.config import sport_by_name, ResultType, discipline_config
from feeds.models.match_meta import MatchMeta
from feeds.models.team import Team
from lib.flag import flag
from lib.response import list_element, button_postback
from .. import api
from lib.mongodb import db
from .model import FeedModel


locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')


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

        match_result_at = match['match_result_at']
        round_mode = match['competition'][0]['season'][0]['round'][0]['round_mode']
        match = match['competition'][0]['season'][0]['round'][0]['match'][0]
        match['match_result_at'] = match_result_at
        match['round_mode'] = round_mode

        match['finished'] = match['finished'] == 'yes'
        match['match_incident'] = match.get('match_incident')

        if 'liveticker' in match:
            del match['liveticker']

        if match['match_time'] == 'unknown':
            match['match_time'] = 'unbekannt'
            datetime_str = '%s %s' % (match['match_date'], '23:59')
        else:
            datetime_str = '%s %s' % (match['match_date'], match['match_time'])

        match['datetime'] = datetime.strptime(
            datetime_str,
            '%Y-%m-%d %H:%M')

        for mr in match.get('match_result', []):
            mr['rank'] = int(mr['rank'])
            mr['match_result'] = int(mr['match_result'])
        return match

    def results_by_country(self, country: str) -> Iterable[FeedModel]:
        """
        Filter end results of this match by country
        :param country: Full name of the country
        :returns:
        """

        yield from (r for r in self.results if r.team.country.name == country)

    def results_by_team(self, team: str) -> Iterable[FeedModel]:
        """
        Filter end results of this match by team
        :param team: Full name of the team
        :returns:
        """

        yield from (r for r in self.results if r.team.name == team)

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
        winner_teams = [winner.team for winner in winner_results]

        for r in winner_results:
            r.match_result = int(r.match_result)

        winning_points = winner_results[0].match_result
        date = datetime.strptime(self.match_date, '%Y-%m-%d')

        config = discipline_config(self.meta.sport, self.meta.discipline_short)
        if isinstance(config, dict) and 'rounds' in config and config['rounds'] \
                and self.meta.event == MatchMeta.Event.OLYMPIA_18:
            header_text = f'++ {self.meta.round_mode} ++ '
        else:
            header_text = ''

        header_text += f'{self.meta.sport}, {self.meta.discipline_short}, {self.meta.gender_name}'
        header_sbtl = f'{day_name[date.weekday()]}, {date.strftime("%d.%m.%Y")} ' \
                      f'um {self.match_time} Uhr in {self.venue.town.name}'

        header = [list_element(
            header_text,
            header_sbtl,
            image_url='https://i.imgur.com/7ZgRGvd.jpg' if self.meta.sport == 'Ski Alpin'
            else 'https://i.imgur.com/Bu05xF6.jpg'
        )]

        for i, (winner_team, winner_result) in enumerate(zip(winner_teams, winner_results)):
            if 'medals' in self.meta and self.meta.medals == 'complete':
                title = f'{Match.medal(i + 1)} '
                image_url = Match.medal_pic(i + 1)

            else:
                title = f'{i+1}. '
                image_url = None

            title += f'{winner_team.name}, {flag(winner_team.country.iso)}' \
                     f' {winner_team.country.code} '
            subtl = f'{self.txt_points(winner_result)}'

            header.append(
                list_element(
                    title,
                    subtl,
                    image_url=image_url))

        return header

    def txt_points(self, result):
        conf = sport_by_name[self.meta.sport]

        if conf.result_type is ResultType.TIME and result.match_result:
            if result.rank == 1:
                point_str = result.match_result
            else:
                point_str = result.match_result - self.winner_result.match_result

            if not point_str:
                return result.comment

            point_str = Match.fmt_millis(point_str, digits=conf.result_digits)

            if result.rank != 1:
                point_str = '+' + point_str

        elif conf.result_type is ResultType.POINTS and result.match_result:
            point_str = locale.format(f'%.{conf.result_digits}f', result.match_result / 100) \
                        + ' Punkte'
        else:
            # TODO TOURNAMENT or empty result.match_result
            point_str = ''
        
        return point_str

    @property
    def btn_podium(self):
        return button_postback('Mehr Platzierungen', {'result_total': self.id, 'step': 'top_10'})

    @property
    def txt_podium(self):
        winner_results = self.results[:3]
        winner_teams = [winner.team for winner in winner_results]

        return '\n'.join(
            '{i} {winner}'.format(
                i=Match.medal(i + 1),
                winner=' '.join([winner_team.name,
                                 flag(winner_team.country.iso),
                                 winner_team.country.code]))
            for i, winner_team in enumerate(winner_teams))

    @staticmethod
    def medal(rank):
        medals = {
            1: '🥇',
            2: '🥈',
            3: '🥉'
        }
        for i in range(4,150):
            medals[i] = str(i)

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

        return f'{dt}.{str(int(micro) // 10 ** (6 - digits)).zfill(digits)}'
