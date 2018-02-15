import random

from feeds.config import SUPPORTED_SPORTS
from feeds.models.person import Person
from feeds.models.subscription import Subscription
from lib.response import list_element, button_postback, quick_reply
from ..handlers.apiaihandler import ApiAiHandler
from ..handlers.payloadhandler import PayloadHandler
from feeds.config import KNOWN_ATHLETES_OLYMPIA

GLOBES = ('🌎', '🌏', '🌍')
KNOWN_ATHLETE_NAMES = {
    (athlete.first_name, athlete.last_name)
    for athlete in KNOWN_ATHLETES_OLYMPIA
}


def state_emoji(subscribed):
    return '✔' if subscribed else '❌'


def api_subscribe(event, parameters, **kwargs):
    sport = parameters.get('sport')
    first_name = parameters.get('first_name')
    last_name = parameters.get('last_name')
    country = parameters.get('country')
    subscription_type = parameters.get('subscription_type')
    athlete = None

    if last_name and first_name:
        if (first_name, last_name) not in KNOWN_ATHLETE_NAMES:
            if not Person.query(firstname=first_name, surname=last_name):
                event.send_text('Diese Person ist leider noch nicht in meiner Datenbank... '
                                'Bist du sicher, dass du dich nicht vertippt hast?')
                return

        athlete = ' '.join([first_name, last_name])

    # TODO: Better logic
    try:
        if (athlete and
            event['message']['nlp']['result']['metadata']['intentName'].endswith('unsubscribe')):
            payload = {'action': 'subscribe', 'filter': athlete}
            result_apply(event, payload)
            return

    except:
        pass

    highlight = subscription_type == 'highlight' or parameters.get('highlight')
    medal = subscription_type == 'medal'
    livestream = subscription_type == 'livestream'

    if highlight:
        payload = {'target': 'highlight', 'state': 'subscribe'}
        highlight_change(event, payload)
        return
    if livestream and sport:
        payload = {'action': 'subscribe', 'filter': sport}
        livestream_apply(event, payload)
        return
    elif livestream and not sport:
        payload = {'action': 'subscribe'}
        livestream_change(event, payload)
        return
    if country:
        payload = {'action': 'subscribe', 'filter': country}
        medal_apply(event, payload)
        return
    elif medal and not country:
        payload = {'action': 'subscribe'}
        livestream_change(event, payload)
    if sport or athlete:
        payload = {'action': 'subscribe', 'filter': sport if sport else athlete}
        result_apply(event, payload)
        return
    elif (last_name and not first_name) or (first_name and not last_name):
        event.send_text('Wenn du dich für die Ergebnisse eines Athleten anmelden möchtest, '
                        'schicke mir den Vor- und Nachnamen. Nur um Verwechslungen zu vermeiden ;)')
        return
    else:
        subs = Subscription.query(psid=event['sender']['id'])
        add = 'Du bist noch für keinen Nachrichten-Service angemeldet. ' if not subs \
            else 'Dies ist die Übersicht deiner angemeldeten Services. '
        event.send_text(f'{add}Du kannst diese jederzeit ändern.')
        send_first_level_subs(event)
        return


def sub_element_livestream(subs):
    type = Subscription.Type.LIVESTREAM
    subscribed = any(sub.type is type for sub in subs)
    buttons = [
        button_postback('🔧 An-/Abmelden' if subscribed else '📝 Anmelden',
                        {'sub': True, type.value: True,
                         'action': 'change' if subscribed else 'subscribe'})
    ]
    sport_list = ', '.join([sub.filter.sport for sub in subs if sub.type is type])
    subtitle = f"{sport_list}" if subscribed else "Push, wenn eine Live-Übertragung beginnt"

    return list_element(f"Livestreams {state_emoji(subscribed)}", subtitle, buttons=buttons)


def livestream_change(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload['action']
    subs = Subscription.query(psid=sender_id, type=Subscription.Type.LIVESTREAM)

    if action == 'subscribe' or len(subs) == 0:
        sports = list_available_sports(subs)
        if not sports:
            send_literal_no_sports_left(event)
            return

        quickreplies = [quick_reply(sport, {'sub': True,
                                            Subscription.Type.LIVESTREAM.value: True,
                                            'filter': sport,
                                            'action': 'subscribe'})
                        for sport in sports[:11]]
        event.send_text(f'Für welche Sportart soll ich dir Bescheid sagen, '
                        f'wenn ein Livestream beginnt?',
                        quickreplies)

    elif action == 'unsubscribe':
        filter_list = [Subscription.describe_filter(sub.filter)
                       for sub in subs if sub.target is Subscription.Target.SPORT]
        quickreplies = [
            quick_reply(filter, {'sub': True,
                                 Subscription.Type.LIVESTREAM.value: True,
                                 'filter': filter,
                                 'action': 'unsubscribe'})
            for filter in filter_list[:11]
        ]
        event.send_text("Für welche Sportart möchtest du keine Meldung "
                        "beim Start eines Livestreams bekommen?",
                        quickreplies)

    elif action == 'change':
        event.send_text("Du bist schon für mindestens eine Sportart angemeldet. Was nun?", [
            quick_reply('✨ Mehr Sportarten', {'sub': True,
                                              Subscription.Type.LIVESTREAM.value: True,
                                              'action': 'subscribe'}),
            quick_reply('❌ Abmelden', {'sub': True,
                                       Subscription.Type.LIVESTREAM.value: True,
                                       'action': 'unsubscribe'}),
        ])


def livestream_apply(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload['action']
    sport = payload['filter']

    if action == 'subscribe':
        Subscription.create(sender_id, Subscription.Target.SPORT, {'sport': sport},
                            Subscription.Type.LIVESTREAM)
        event.send_text("Super! Ich sage dir, wenn's losgeht.\n"
                        "Wenn du dich für weitere Übertragungen im Livestream interessierst, "
                        "schreib mir einfach z.B. \'Anmelden für Biathlon Livestream\'.")
        event.send_text("Hier deine Übersicht:")
        send_first_level_subs(event)
    elif action == 'unsubscribe':
        sub = Subscription.query(psid=sender_id,
                                 type=Subscription.Type.LIVESTREAM,
                                 target=Subscription.Target.SPORT,
                                 filter={'sport': sport})
        if len(sub) != 1:
            raise Exception("Subscription not found, but offered in quick reply. Weird!")

        Subscription.delete(_id=sub[0]._id)
        event.send_text(f"Gut. Ich höre auf, dich wegen {sport}-Livestreams zu nerven.")


def sub_element_medal(subs):
    type = Subscription.Type.MEDAL
    subscribed = any(sub.type is type for sub in subs)
    buttons = [
        button_postback('🔧 An-/Abmelden' if subscribed else '📝 Anmelden',
                        {'sub': True, type.value: True,
                         'action': 'change' if subscribed else 'subscribe'})
    ]
    country_list = ', '.join([sub.filter.country for sub in subs if sub.type is type])
    subtitle = f"{country_list}" if subscribed \
        else "Push, wenn ein gewähltes Land eine Medaille gewinnt"

    return list_element(f"Medaillen {state_emoji(subscribed)}", subtitle, buttons=buttons)


def medal_change(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload['action']
    subs = Subscription.query(psid=sender_id, type=Subscription.Type.MEDAL)

    if action == 'subscribe' or len(subs) == 0:
        event.send_text('Du kannst dich ganz einfach für die Medaillen-Benachrichtigungen '
                        f'anmelden {random.choice(GLOBES)} Dafür musst du mir z. B. '
                        f'folgendes schreiben:\n\n "Anmelden für Medaillen von Deutschland"')

    elif action == 'unsubscribe':
        filter_list = [Subscription.describe_filter(sub.filter)
                       for sub in subs if sub.target is Subscription.Target.COUNTRY]
        quickreplies = [
            quick_reply(filter, {'sub': True,
                                 Subscription.Type.MEDAL.value: True,
                                 'filter': filter,
                                 'action': 'unsubscribe'})
            for filter in filter_list[:11]
        ]
        event.send_text("Für welches Land möchtest du keine Infos mehr bekommen?",
                        quickreplies)

    elif action == 'change':
        event.send_text("Du bist schon für mindestens ein Land angemeldet. Was nun?", [
            quick_reply('✨ Mehr Länder', {'sub': True,
                                          Subscription.Type.MEDAL.value: True,
                                          'action': 'subscribe'}),
            quick_reply('❌ Abmelden', {'sub': True,
                                       Subscription.Type.MEDAL.value: True,
                                       'action': 'unsubscribe'}),
        ])


def medal_apply(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload['action']
    country = payload['filter']

    if action == 'subscribe':
        Subscription.create(sender_id, Subscription.Target.COUNTRY,
                            {'country': country}, Subscription.Type.MEDAL)
        event.send_text(f'Cool! Wann immer {country} eine Olympische Medaille erkämpft, sage ich '
                        'dir Bescheid!\nDich interessiert noch ein andees Land? Schreib mir '
                        'einfach z.B. \'Anmelden für Schweden\'.')
        send_second_level_subs(event)
    elif action == 'unsubscribe':
        sub = Subscription.query(psid=sender_id,
                                 type=Subscription.Type.MEDAL,
                                 target=Subscription.Target.COUNTRY,
                                 filter={'country': country})
        if len(sub) != 1:
            raise Exception("Subscription not found, but offered in quick reply. Weird!")

        Subscription.delete(_id=sub[0]._id)
        event.send_text(f'Du bekommst ab jetzt keine Benachrichtigungen über Medaillen '
                        f'des Landes "{country}"')
        send_second_level_subs(event)


def sub_element_sport(subs):
    target = Subscription.Target.SPORT
    subscribed = any(sub.target is target for sub in subs)
    buttons = [
        button_postback('🔧 An-/Abmelden' if subscribed else '📝 Anmelden',
                        {'sub': True, target.value: True,
                         'action': 'change' if subscribed else 'subscribe'})
    ]
    sport_list = ', '.join([sub.filter.sport for sub in subs if sub.target is target])
    subtitle = f"{sport_list}" if subscribed \
        else "Push, bei Ergebnissen und Neuigkeiten in der gewählten Sportart"

    return list_element(f"Sportart {state_emoji(subscribed)}", subtitle, buttons=buttons)


def sport_change(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload['action']
    subs = Subscription.query(psid=sender_id,
                              type=Subscription.Type.RESULT,
                              target=Subscription.Target.SPORT)

    if action == 'subscribe' or len(subs) == 0:
        sports = list_available_sports(subs)
        if not sports:
            send_literal_no_sports_left(event)
            return

        quickreplies = [quick_reply(sport, {'sub': True,
                                            Subscription.Type.RESULT.value: True,
                                            'filter': sport,
                                            'action': 'subscribe'})
                        for sport in sports[:11]]
        event.send_text(f'Ich sage Bescheid, sobald ich Ergbnisse oder oder Neuigkeiten habe. '
                        f'Für welche Sportart interessierst du dich?',
                        quickreplies)

    elif action == 'unsubscribe':
        filter_list = [Subscription.describe_filter(sub.filter)
                       for sub in subs if sub.target is Subscription.Target.SPORT]
        quickreplies = [
            quick_reply(filter, {'sub': True,
                                 Subscription.Type.RESULT.value: True,
                                 'filter': filter,
                                 'action': 'unsubscribe'})
            for filter in filter_list[:11]
        ]
        event.send_text("Für welche Sportart möchtest du keine Infos mehr bekommen?",
                        quickreplies)

    elif action == 'change':
        event.send_text("Du bist schon für mindestens eine Sportart angemeldet. Was nun?", [
            quick_reply('✨ Mehr Sportarten', {'sub': True,
                                              Subscription.Target.SPORT.value: True,
                                              'action': 'subscribe'}),
            quick_reply('❌ Abmelden', {'sub': True,
                                       Subscription.Target.SPORT.value: True,
                                       'action': 'unsubscribe'}),
        ])


def sub_element_athlete(subs):
    target = Subscription.Target.ATHLETE
    subscribed = any(sub.target is target for sub in subs)
    buttons = [
        button_postback('🔧 An-/Abmelden' if subscribed else '📝 Anmelden',
                        {'sub': True, target.value: True,
                         'action': 'change' if subscribed else 'subscribe'})
    ]
    athlete_list = ', '.join([sub.filter.athlete for sub in subs if sub.target is target])
    subtitle = f"{athlete_list}" if subscribed \
        else "Push, bei Ergebnissen und Neuigkeiten für einen gewählten Sportler"

    return list_element(f"Sportler {state_emoji(subscribed)}", subtitle, buttons=buttons)


def athlete_change(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload['action']
    subs = Subscription.query(psid=sender_id,
                              type=Subscription.Type.RESULT,
                              target=Subscription.Target.ATHLETE)

    if action == 'subscribe' or len(subs) == 0:
        event.send_text("Über wen soll ich dich informieren? Schreibe mir zum Beispiel "
                        "\'Anmelden für Viktoria Rebensburg\' - bitte nenne immer den "
                        "Vor- und Nachnamen, damit es keine Missverständnisse gibt.")

    elif action == 'unsubscribe':
        filter_list = [Subscription.describe_filter(sub.filter)
                       for sub in subs if sub.target is Subscription.Target.ATHLETE]
        quickreplies = [
            quick_reply(filter, {'sub': True,
                                 Subscription.Type.RESULT.value: True,
                                 'filter': filter,
                                 'action': 'unsubscribe'})
            for filter in filter_list[:11]
        ]
        event.send_text("Für welchen Sportler möchtest du keine Infos mehr bekommen?",
                        quickreplies)

    elif action == 'change':
        event.send_text("Du bist schon für mindestens einen Sportler angemeldet. Was nun?", [
            quick_reply('✨ Mehr Sportler', {'sub': True,
                                            Subscription.Target.ATHLETE.value: True,
                                            'action': 'subscribe'}),
            quick_reply('❌ Abmelden', {'sub': True,
                                       Subscription.Target.ATHLETE.value: True,
                                       'action': 'unsubscribe'}),
        ])


def result_apply(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload['action']
    filter = payload['filter']

    target = Subscription.Target.SPORT if filter in SUPPORTED_SPORTS \
        else Subscription.Target.ATHLETE
    sub_filter = {'sport': filter} if filter in SUPPORTED_SPORTS else {'athlete': filter}

    if action == 'subscribe':
        Subscription.create(sender_id, target, sub_filter, Subscription.Type.RESULT)
        reply = f"\nWenn du dich für weitere Ergebnis-Dienste anmelden möchtest, " \
                f"schreibe mir einfach z.B. 'Anmelden für " \
                f"{'Biathlon' if filter in SUPPORTED_SPORTS else 'Viktoria Rebensburg'}.'"
        event.send_text("Super! Ich sage dir, sobald es etwas Neues gibt." + reply)
        send_second_level_subs(event)
    elif action == 'unsubscribe':
        sub = Subscription.query(psid=sender_id,
                                 type=Subscription.Type.RESULT,
                                 target=target,
                                 filter=sub_filter)
        if len(sub) != 1:
            raise Exception("Subscription not found, but offered in quick reply. Weird!")

        Subscription.delete(_id=sub[0]._id)
        event.send_text(f"Gut. Ich höre auf, dich mit {filter} Infos zu nerven.")
        send_second_level_subs(event)


def highlight_change(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['state']
    subs = Subscription.query(psid=sender_id, type=Subscription.Type.HIGHLIGHT)

    if state == 'subscribe':
        target = Subscription.Target.HIGHLIGHT
        filter_arg = {}
        filter_arg['highlight'] = 'Highlight'
        type_arg = Subscription.Type.HIGHLIGHT
        Subscription.create(sender_id, target, filter_arg, type_arg)
        event.send_text('#läuft\nIch melde mich während der Olympischen Spiele zweimal täglich mit '
                        'den Highlights aus PyeonChang bei dir.\nKann ich sonst nochwas liefern?')
        send_first_level_subs(event)
    elif state == 'unsubscribe':
        for sub in subs:
            Subscription.delete(_id=sub._id)
        event.send_text('Du bist nun von den Highlights abgemeldet.')
        send_first_level_subs(event)


def pld_subscriptions(event, payload, **kwargs):
    send_first_level_subs(event)


def send_first_level_subs(event, **kwargs):
    sender_id = event['sender']['id']
    subs = Subscription.query(psid=sender_id)

    if any(sub.target is Subscription.Target.HIGHLIGHT for sub in subs):
        highlight_emoji, highlight_button = '✔', button_postback('📝 Abmelden',
                                                                 {'target': 'highlight',
                                                                  'state': 'unsubscribe'})
    else:
        highlight_emoji, highlight_button = '❌', button_postback('📝 Anmelden',
                                                                 {'target': 'highlight',
                                                                  'state': 'subscribe'})

    if any(sub.type is Subscription.Type.RESULT for sub in subs):
        result_button = button_postback('🔧 An-/Abmelden', {'type': 'result'})
        result_emoji = '✔'
    else:
        result_button = button_postback('📝 Anmelden', {'type': 'result'})
        result_emoji = '❌'

    elements = [
        list_element(
            'Highlights des Tages ' + highlight_emoji,
            'Tägliche Zusammenfassungen für Olympia',
            buttons=[highlight_button]),
        list_element(
            'Ergebnisdienst ' + result_emoji,
            'Sportart / Sportler / Medaillen',
            buttons=[result_button]),
        sub_element_livestream(subs),
    ]

    event.send_list(elements)


def send_second_level_subs(event, **kwargs):
    sender_id = event['sender']['id']
    subs = (Subscription.query(type=Subscription.Type.RESULT, psid=sender_id) +
            Subscription.query(type=Subscription.Type.MEDAL, psid=sender_id))

    elements = [
        sub_element_sport(subs),
        sub_element_athlete(subs),
        sub_element_medal(subs),
    ]

    event.send_list(elements)


def list_available_sports(subs):
    filters = {Subscription.describe_filter(sub.filter)
               for sub in subs if sub.target is Subscription.Target.SPORT}
    return [sport for sport in SUPPORTED_SPORTS if sport not in filters]


def send_literal_no_sports_left(event):
    event.send_text(f'Du bist bereits für alle möglichen Sportarten '
                    f'angemeldet. Du scheinst ja genau so ein '
                    f'Wintersport Nerd zu sein wie ich 🤓')


handlers = [
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe', follow_up=True),
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe'),
    ApiAiHandler(api_subscribe, 'push.subscription.unsubscribe'),
    PayloadHandler(livestream_apply, ['sub', Subscription.Type.LIVESTREAM.value, 'filter', 'action']),
    PayloadHandler(livestream_change, ['sub', Subscription.Type.LIVESTREAM.value, 'action']),
    PayloadHandler(result_apply, ['sub', Subscription.Type.RESULT.value, 'filter', 'action']),
    PayloadHandler(sport_change, ['sub', Subscription.Target.SPORT.value, 'action']),
    PayloadHandler(athlete_change, ['sub', Subscription.Target.ATHLETE.value, 'action']),
    PayloadHandler(medal_apply, ['sub', Subscription.Type.MEDAL.value, 'filter', 'action']),
    PayloadHandler(medal_change, ['sub', Subscription.Type.MEDAL.value, 'action']),
    PayloadHandler(highlight_change, ['target', 'state']),
    PayloadHandler(send_second_level_subs, ['type']),
    PayloadHandler(pld_subscriptions, ['send_subscriptions']),
]
