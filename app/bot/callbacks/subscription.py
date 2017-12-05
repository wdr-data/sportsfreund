from ..handlers.payloadhandler import PayloadHandler
from ..fb import send_text, send_list, list_element, button_postback, send_buttons
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
    subscribe_flow(event, sport, discipline)


def subscribe_flow(event, sport, discipline=None):
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
    unsubscribe_flow(event)


def unsubscribe_flow(event):
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
                                                                 {'target': 'highlight',
                                                                  'state': 'unsubscribe'})
    else:
        highlight_emoji, highlight_button = '❌', button_postback('Anmelden',
                                                                 {'target': 'highlight',
                                                                  'state': 'subscribe'})

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
            buttons=[button_postback('🔧 Ändern', {'type': 'result'})])
    ]

    send_list(
        sender_id,
        elements,
    )


def manage_subscriptions(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['state']
    target = payload['target']

    if target == 'highlight':
        if state == 'subscribe':
            send_text(sender_id,
                      'Diese Funktion ist erst zu den Olympischen Winterspielen verfügbar.')
        elif state == 'unsubscribe':
            send_text(sender_id,
                      'Diese Funktion ist erst zu den Olympischen Winterspielen verfügbar.')


def change_subscriptions(event, payload, **kwargs):
    sender_id = event['sender']['id']
    type = payload['type']
    offset = payload.get('offset', 0)
    subs = Subscription.query(psid=sender_id, type=type)

    if len(subs) == 0:
        send_text(sender_id, 'Du bist noch für keinen Nachrichten Dienst angemeldet.')
        return
    elif len(subs) == 1:
        send_buttons(sender_id,
                     f'Du bist für den Nachrichten Dienst {type} zum Thema '
                     f'{Subscription.describe_filter(subs[0].filter)} angemeldet. '
                     f'Möchtest du dich abmelden?',
                     button_postback('Abmelden', ['unsubscribe']))
        return

    num_subs = 4
    if len(subs) - (offset + num_subs) == 1:
        num_subs = 3

    elements = [
        list_element(Subscription.describe_filter(sub.filter),
                     button_postback('Abmelden', {'unsubscribe': str(sub._id)}))
        for sub in subs[offset:offset + num_subs]
    ]

    if len(subs) - offset > num_subs:
        new_payload = payload.copy()
        new_payload['offset'] = offset + num_subs
        button = button_postback('Mehr anzeigen', new_payload)
    else:
        button = None

    send_list(sender_id, elements, button=button)



handlers = [
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe', follow_up=True),
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe'),
    PayloadHandler(manage_subscriptions, ['target', 'state']),
    PayloadHandler(change_subscriptions, ['type'])
]
