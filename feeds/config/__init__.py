import yaml

with open('discipline_aliases.yml', 'r') as f:
    DISCIPLINE_ALIASES = yaml.load(f)

with open('sports_config.yml', 'r') as f:
    SPORTS_CONFIG = yaml.load(f)
