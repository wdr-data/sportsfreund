import os
from pathlib import Path
from enum import Enum

import yaml

from lib.model import DotDict

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))


class ResultType(Enum):
    TIME = 'time'
    POINTS = 'points'


class CompetitionType(Enum):
    SINGLE = 'single'
    RACE = 'race'
    TOURNAMENT = 'tournament'
    ROBIN = 'robin'


with open(BASE_DIR / 'discipline_aliases.yml', 'rb') as f:
    DISCIPLINE_ALIASES = DotDict(yaml.load(f))

with open(BASE_DIR / 'sports_config.yml', 'rb') as f:
    SPORTS_CONFIG = [DotDict(sport) for sport in yaml.load(f)]

with open(BASE_DIR / 'german_athletes_olympia.yml', 'rb') as f:
    GERMAN_ATHLETES_OLYMPIA = [DotDict(athlete) for athlete in yaml.load(f)]

for sport in SPORTS_CONFIG:
    sport.result_type = ResultType(sport.result_type.lower())

    for discipline in sport.disciplines:
        discipline.competition_type = CompetitionType(discipline.competition_type.lower())

sport_by_name = {
    sport.name: sport
    for sport in SPORTS_CONFIG
}


def discipline_config(sport, discipline):
    for sport_config in SPORTS_CONFIG:
        if sport_config.name == sport:
            for dis in sport_config.disciplines:
                if dis.name == discipline:
                    conf = dis
                    conf['result_type'] = sport_config['result_type']
                    conf['sport'] = sport
                    return conf

    return None

supported_sports = [
    sport.name for sport in SPORTS_CONFIG
]