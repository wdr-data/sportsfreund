from prometheus_client import Gauge

from feeds.models.subscription import Subscription

g = Gauge('subscriptions', 'User subscriptions to different services', ['type', 'target', 'filter'])


def collect():
    subs = Subscription.collection.aggregate([
        {'$group': {'_id': {'type': '$type', 'target': '$target', 'filter': '$filter'}, 'count': {'$sum': 1}}}
    ])
    for sub in subs:
        group = sub['_id']
        g.labels(group['type'], group['target'], Subscription.describe_filter(group['filter'])).set(sub['count'])
