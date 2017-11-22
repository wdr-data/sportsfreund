
"""
Basic tests for models and caching.

You can paste this file into a python shell you start with
docker-compose run web python
"""

from feeds.models.match import *
from feeds.models.team import *
from feeds.models.venue import *
from feeds.models.sport import *
from feeds.models.season import *
from feeds.models.competition import *
from feeds.models.topic import *

import sys
import logging
from feeds import api

api.logger.addHandler(logging.StreamHandler(sys.stdout))
Model.logger.addHandler(logging.StreamHandler(sys.stdout))

ma = Match.by_id(8471268, clear_cache=True)
ma = Match.by_id(8471268)
ma.id

te = Team.by_id(26973, clear_cache=True)
te = Team.by_id(26973)
te.id

ve = Venue.by_id(2547, clear_cache=True)
ve = Venue.by_id(2547)
ve.id

sp = Sport.by_id(43, clear_cache=True)
sp = Sport.by_id(43)
sp.id

se = Season.by_id(24806, clear_cache=True)
se = Season.by_id(24806)
se.id

co = Competition.by_id(789, clear_cache=True)
co = Competition.by_id(789)
co.id

to = Topic.by_id(1773, clear_cache=True)
to = Topic.by_id(1773)
to.id

