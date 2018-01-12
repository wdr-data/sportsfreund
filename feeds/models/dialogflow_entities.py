
"""
Basic tests for models and caching.

You can paste this file into a python shell you start with
docker-compose run web python
"""

from feeds.models.match_meta import MatchMeta
import re

s = MatchMeta.search_range(sport='Skispringen')
t = str(s)

item_list = list(sorted(set(re.findall(r'"discipline_short": "(.*?)"', t.replace("'",'"'), re.DOTALL))))


item_list = list(sorted(set(re.findall(r'"discipline": {[^}]*?"name": "(.*?)"', t.replace("'",'"'), re.DOTALL))))

entities = []
for item in item_list:
    entities.append({
        "value": item,
        "synonyms": [item]
    })
