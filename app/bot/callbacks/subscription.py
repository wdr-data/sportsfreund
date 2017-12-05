from ..fb import send_text, send_list, list_element, button_postback
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
    subscribe(event, sport, discipline)


def subscribe(event, sport, discipline=None):
    sender_id = event['sender']['id']

    target = Subscription.Target.SPORT if sport else Subscription.Target.DISCIPLINE

    filter_arg = {'sport': sport}

    if discipline:
        filter_arg['discipline'] = discipline

    type_arg = Subscription.Type.RESULT

    Subscription.create(sender_id, target, filter_arg, type_arg)

    send_text(sender_id,
              'Vielen Dank für deine Anmeldung. In folgender Liste siehst du alle Themen, '
              'über die ich dich automatisch informiere. Du kannst sie jederzeit ändern.')
    send_subscriptions(event)


def api_unsubscribe(event, parameters, **kwargs):
    unsubscribe(event)

def unsubscribe(event):
    sender_id = event['sender']['id']
    send_text(sender_id,
              'Du möchtest dich von automatischen Nachrichten abmelden - OK. '
              'In der Liste siehst du alle deine Anmeldungen. '
              'Du kannst Sie jederzeit über die Buttons ändern.')
    send_subscriptions(event)


def send_subscriptions(event, **kwargs):
    sender_id = event['sender']['id']
    subs = Subscription.query(psid=sender_id)

    if any(sub.target is Subscription.Target.HIGHLIGHT for sub in subs):
        highlight_emoji, highlight_button = '✔', button_postback('Abmelden',
                                                                 ['highlight_subscribe'])
    else:
        highlight_emoji, highlight_button = '❌', button_postback('Anmelden',
                                                                 ['highlight_unsubscribe'])

    if any(sub.type is Subscription.Type.RESULT for sub in subs):
        result_subtitle = ', '.join(
            [Subscription.describe_filter(sub.filter)
             for sub in subs if sub.type is Subscription.Type.RESULT])

        if len(result_subtitle) > 80:
            result_subtitle = result_subtitle[:77] + '...'

        result_emoji = '✔'
    else:
        result_subtitle = 'Nicht angemeldet'
        result_emoji = '❌'

    elements = [
        list_element(
            'Highlights des Tages ' + highlight_emoji,
            'TODO: Text festlegen',
            buttons=[highlight_button]),
        list_element(
            'Ergebnisdienst ' + result_emoji,
            result_subtitle,
            buttons=[button_postback('🔧 Ändern', ['result_subscriptions'])])
    ]

    send_list(
        sender_id,
        elements,
    )


handlers = [
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe', follow_up=True)
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe')
]
