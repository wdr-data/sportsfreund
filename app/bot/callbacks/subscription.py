from ..fb import send_text
from ..handlers.apiaihandler import ApiAiHandler
from feeds.models.subscription import Subscription


def api_subscribe(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')

    if not sport:
        send_text(sender_id,
                  'Magst du dich für Biathlon oder Ski-Alpin Ergebnisse anmelden?')
        return

    target = Subscription.Target.SPORT if sport else Subscription.Target.DISCIPLINE

    filter_arg = {'sport': sport}

    if discipline:
        filter_arg['discipline'] = discipline

    type_arg = Subscription.Type.RESULT

    Subscription.create(sender_id, target, filter_arg, type_arg)


handlers = [
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe', follow_up=True)
]

