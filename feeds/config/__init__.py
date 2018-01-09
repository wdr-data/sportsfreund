import os
from pathlib import Path

import yaml

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

with open(BASE_DIR / 'discipline_aliases.yml', 'r') as f:
    DISCIPLINE_ALIASES = yaml.load(f)

with open(BASE_DIR / 'sports_config.yml', 'r') as f:
    SPORTS_CONFIG = yaml.load(f)
