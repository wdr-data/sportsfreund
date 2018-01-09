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


with open(BASE_DIR / 'discipline_aliases.yml', 'r') as f:
    DISCIPLINE_ALIASES = DotDict(yaml.load(f))

with open(BASE_DIR / 'sports_config.yml', 'r') as f:
    SPORTS_CONFIG = [DotDict(sport) for sport in yaml.load(f)]

for sport in SPORTS_CONFIG:
    sport.result_type = ResultType(sport.result_type.lower())

    for discipline in sport.disciplines:
        discipline.competition_type = CompetitionType(discipline.competition_type.lower())

sport_by_name = {
    sport.name: sport
    for sport in SPORTS_CONFIG
}
