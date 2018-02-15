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
TXT_NO_SPORTS_LEFT = ('Du bist bereits für alle möglichen Sportarten angemeldet. Du scheinst ja '
                      'genau so ein Wintersport Nerd zu sein wie ich 🤓')
KEY_ACTION = 'action'
KEY_FILTER = 'filter'
KEY_TARGET = 'target'
KEY_STATE = 'state'
KEY_SUB = 'sub'
KEY_TYPE = 'type'
KEY_RESULT = 'result'
ACT_SUBSCRIBE = 'subscribe'
ACT_UNSUBSCRIBE = 'unsubscribe'
ACT_CHANGE = 'change'
TAR_HIGHLIGHT = 'highlight'
TAR_SPORT = 'sport'
TAR_ATHLETE = 'athlete'
TAR_COUNTRY = 'country'
TYP_HIGHLIGHT = 'highlight'
TYP_MEDAL = 'medal'
TYP_LIVESTREAM = 'livestream'


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
            payload = {KEY_ACTION: ACT_SUBSCRIBE, KEY_FILTER: athlete}
            result_apply(event, payload)
            return

    except:
        pass

    highlight = subscription_type == TYP_HIGHLIGHT
    medal = subscription_type == TYP_MEDAL
    livestream = subscription_type == TYP_LIVESTREAM

    if highlight:
        payload = {KEY_TARGET: TAR_HIGHLIGHT, KEY_STATE: ACT_SUBSCRIBE}
        highlight_change(event, payload)
        return
    if livestream and sport:
        payload = {KEY_ACTION: ACT_SUBSCRIBE, KEY_FILTER: sport}
        livestream_apply(event, payload)
        return
    elif livestream and not sport:
        payload = {KEY_ACTION: ACT_SUBSCRIBE}
        livestream_change(event, payload)
        return
    if country:
        payload = {KEY_ACTION: ACT_SUBSCRIBE, KEY_FILTER: country}
        medal_apply(event, payload)
        return
    elif medal and not country:
        payload = {KEY_ACTION: ACT_SUBSCRIBE}
        livestream_change(event, payload)
    if sport or athlete:
        payload = {KEY_ACTION: ACT_SUBSCRIBE, KEY_FILTER: sport if sport else athlete}
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
                        {KEY_SUB: True, type.value: True,
                         KEY_ACTION: ACT_CHANGE if subscribed else ACT_SUBSCRIBE})
    ]
    sport_list = ', '.join(sub.filter.sport for sub in subs if sub.type is type)
    subtitle = f"{sport_list}" if subscribed else "Push, wenn eine Live-Übertragung beginnt"

    return list_element(f"Livestreams {state_emoji(subscribed)}", subtitle, buttons=buttons)


def livestream_change(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload[KEY_ACTION]
    subs = Subscription.query(psid=sender_id, type=Subscription.Type.LIVESTREAM)

    if action == ACT_SUBSCRIBE or len(subs) == 0:
        sports = list_available_sports(subs)
        if not sports:
            event.send_text(TXT_NO_SPORTS_LEFT)
            return

        quickreplies = [quick_reply(sport, {KEY_SUB: True,
                                            Subscription.Type.LIVESTREAM.value: True,
                                            KEY_FILTER: sport,
                                            KEY_ACTION: ACT_SUBSCRIBE})
                        for sport in sports[:11]]
        event.send_text(f'Für welche Sportart soll ich dir Bescheid sagen, '
                        f'wenn ein Livestream beginnt?',
                        quickreplies)

    elif action == ACT_UNSUBSCRIBE:
        filter_list = [Subscription.describe_filter(sub.filter)
                       for sub in subs if sub.target is Subscription.Target.SPORT]
        quickreplies = [
            quick_reply(filter, {KEY_SUB: True,
                                 Subscription.Type.LIVESTREAM.value: True,
                                 KEY_FILTER: filter,
                                 KEY_ACTION: ACT_UNSUBSCRIBE})
            for filter in filter_list[:11]
        ]
        event.send_text("Für welche Sportart möchtest du keine Meldung "
                        "beim Start eines Livestreams bekommen?",
                        quickreplies)

    elif action == ACT_CHANGE:
        event.send_text("Du bist schon für mindestens eine Sportart angemeldet. Was nun?", [
            quick_reply('✨ Mehr Sportarten', {KEY_SUB: True,
                                              Subscription.Type.LIVESTREAM.value: True,
                                              KEY_ACTION: ACT_SUBSCRIBE}),
            quick_reply('❌ Abmelden', {KEY_SUB: True,
                                       Subscription.Type.LIVESTREAM.value: True,
                                       KEY_ACTION: ACT_UNSUBSCRIBE}),
        ])


def livestream_apply(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload[KEY_ACTION]
    sport = payload[KEY_FILTER]

    if action == ACT_SUBSCRIBE:
        Subscription.create(sender_id, Subscription.Target.SPORT,
                            {Subscription.Target.SPORT.value: sport},
                            Subscription.Type.LIVESTREAM)
        event.send_text("Super! Ich sage dir, wenn's losgeht.\n"
                        "Wenn du dich für weitere Übertragungen im Livestream interessierst, "
                        "schreib mir einfach z.B. \'Anmelden für Biathlon Livestream\'.")
        event.send_text("Hier deine Übersicht:")
        send_first_level_subs(event)
    elif action == ACT_UNSUBSCRIBE:
        sub = Subscription.query(psid=sender_id,
                                 type=Subscription.Type.LIVESTREAM,
                                 target=Subscription.Target.SPORT,
                                 filter={Subscription.Target.SPORT.value: sport})
        if len(sub) != 1:
            raise Exception("Subscription not found, but offered in quick reply. Weird!")

        Subscription.delete(_id=sub[0]._id)
        event.send_text(f"Gut. Ich höre auf, dich wegen {sport}-Livestreams zu nerven.")


def sub_element_medal(subs):
    type = Subscription.Type.MEDAL
    subscribed = any(sub.type is type for sub in subs)
    buttons = [
        button_postback('🔧 An-/Abmelden' if subscribed else '📝 Anmelden',
                        {KEY_SUB: True, type.value: True,
                         KEY_ACTION: ACT_CHANGE if subscribed else ACT_SUBSCRIBE})
    ]
    country_list = ', '.join([sub.filter.country for sub in subs if sub.type is type])
    subtitle = f"{country_list}" if subscribed \
        else "Push, wenn ein gewähltes Land eine Medaille gewinnt"

    return list_element(f"Medaillen {state_emoji(subscribed)}", subtitle, buttons=buttons)


def medal_change(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload[KEY_ACTION]
    subs = Subscription.query(psid=sender_id, type=Subscription.Type.MEDAL)

    if action == ACT_SUBSCRIBE or len(subs) == 0:
        event.send_text('Du kannst dich ganz einfach für die Medaillen-Benachrichtigungen '
                        f'anmelden {random.choice(GLOBES)} Dafür musst du mir z. B. '
                        f'folgendes schreiben:\n\n "Anmelden für Medaillen von Deutschland"')

    elif action == ACT_UNSUBSCRIBE:
        filter_list = [Subscription.describe_filter(sub.filter)
                       for sub in subs if sub.target is Subscription.Target.COUNTRY]
        quickreplies = [
            quick_reply(filter, {KEY_SUB: True,
                                 Subscription.Type.MEDAL.value: True,
                                 KEY_FILTER: filter,
                                 KEY_ACTION: ACT_UNSUBSCRIBE})
            for filter in filter_list[:11]
        ]
        event.send_text("Für welches Land möchtest du keine Infos mehr bekommen?",
                        quickreplies)

    elif action == ACT_CHANGE:
        event.send_text("Du bist schon für mindestens ein Land angemeldet. Was nun?", [
            quick_reply('✨ Mehr Länder', {KEY_SUB: True,
                                          Subscription.Type.MEDAL.value: True,
                                          KEY_ACTION: ACT_SUBSCRIBE}),
            quick_reply('❌ Abmelden', {KEY_SUB: True,
                                       Subscription.Type.MEDAL.value: True,
                                       KEY_ACTION: ACT_UNSUBSCRIBE}),
        ])


def medal_apply(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload[KEY_ACTION]
    country = payload[KEY_FILTER]

    if action == ACT_SUBSCRIBE:
        Subscription.create(sender_id, Subscription.Target.COUNTRY,
                            {Subscription.Target.COUNTRY.value: country}, Subscription.Type.MEDAL)
        event.send_text(f'Cool! Wann immer {country} eine Olympische Medaille erkämpft, sage ich '
                        'dir Bescheid!\nDich interessiert noch ein andees Land? Schreib mir '
                        'einfach z.B. \'Anmelden für Schweden\'.')
        send_second_level_subs(event)
    elif action == ACT_UNSUBSCRIBE:
        sub = Subscription.query(psid=sender_id,
                                 type=Subscription.Type.MEDAL,
                                 target=Subscription.Target.COUNTRY,
                                 filter={Subscription.Target.COUNTRY.value: country})
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
                        {KEY_SUB: True, target.value: True,
                         KEY_ACTION: ACT_CHANGE if subscribed else ACT_SUBSCRIBE})
    ]
    sport_list = ', '.join([sub.filter.sport for sub in subs if sub.target is target])
    subtitle = f"{sport_list}" if subscribed \
        else "Push, bei Ergebnissen und Neuigkeiten in der gewählten Sportart"

    return list_element(f"Sportart {state_emoji(subscribed)}", subtitle, buttons=buttons)


def sport_change(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload[KEY_ACTION]
    subs = Subscription.query(psid=sender_id,
                              type=Subscription.Type.RESULT,
                              target=Subscription.Target.SPORT)

    if action == ACT_SUBSCRIBE or len(subs) == 0:
        sports = list_available_sports(subs)
        if not sports:
            event.send_text(TXT_NO_SPORTS_LEFT)
            return

        quickreplies = [quick_reply(sport, {KEY_SUB: True,
                                            Subscription.Type.RESULT.value: True,
                                            KEY_FILTER: sport,
                                            KEY_ACTION: ACT_SUBSCRIBE})
                        for sport in sports[:11]]
        event.send_text(f'Ich sage Bescheid, sobald ich Ergbnisse oder oder Neuigkeiten habe. '
                        f'Für welche Sportart interessierst du dich?',
                        quickreplies)

    elif action == ACT_UNSUBSCRIBE:
        filter_list = [Subscription.describe_filter(sub.filter)
                       for sub in subs if sub.target is Subscription.Target.SPORT]
        quickreplies = [
            quick_reply(filter, {KEY_SUB: True,
                                 Subscription.Type.RESULT.value: True,
                                 KEY_FILTER: filter,
                                 KEY_ACTION: ACT_UNSUBSCRIBE})
            for filter in filter_list[:11]
        ]
        event.send_text("Für welche Sportart möchtest du keine Infos mehr bekommen?",
                        quickreplies)

    elif action == ACT_CHANGE:
        event.send_text("Du bist schon für mindestens eine Sportart angemeldet. Was nun?", [
            quick_reply('✨ Mehr Sportarten', {KEY_SUB: True,
                                              Subscription.Target.SPORT.value: True,
                                              KEY_ACTION: ACT_SUBSCRIBE}),
            quick_reply('❌ Abmelden', {KEY_SUB: True,
                                       Subscription.Target.SPORT.value: True,
                                       KEY_ACTION: ACT_UNSUBSCRIBE}),
        ])


def sub_element_athlete(subs):
    target = Subscription.Target.ATHLETE
    subscribed = any(sub.target is target for sub in subs)
    buttons = [
        button_postback('🔧 An-/Abmelden' if subscribed else '📝 Anmelden',
                        {KEY_SUB: True, target.value: True,
                         KEY_ACTION: ACT_CHANGE if subscribed else ACT_SUBSCRIBE})
    ]
    athlete_list = ', '.join([sub.filter.athlete for sub in subs if sub.target is target])
    subtitle = f"{athlete_list}" if subscribed \
        else "Push, bei Ergebnissen und Neuigkeiten für einen gewählten Sportler"

    return list_element(f"Sportler {state_emoji(subscribed)}", subtitle, buttons=buttons)


def athlete_change(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload[KEY_ACTION]
    subs = Subscription.query(psid=sender_id,
                              type=Subscription.Type.RESULT,
                              target=Subscription.Target.ATHLETE)

    if action == ACT_SUBSCRIBE or len(subs) == 0:
        event.send_text("Über wen soll ich dich informieren? Schreibe mir zum Beispiel "
                        "\'Anmelden für Viktoria Rebensburg\' - bitte nenne immer den "
                        "Vor- und Nachnamen, damit es keine Missverständnisse gibt.")

    elif action == ACT_UNSUBSCRIBE:
        filter_list = [Subscription.describe_filter(sub.filter)
                       for sub in subs if sub.target is Subscription.Target.ATHLETE]
        quickreplies = [
            quick_reply(filter, {KEY_SUB: True,
                                 Subscription.Type.RESULT.value: True,
                                 KEY_FILTER: filter,
                                 KEY_ACTION: ACT_UNSUBSCRIBE})
            for filter in filter_list[:11]
        ]
        event.send_text("Für welchen Sportler möchtest du keine Infos mehr bekommen?",
                        quickreplies)

    elif action == ACT_CHANGE:
        event.send_text("Du bist schon für mindestens einen Sportler angemeldet. Was nun?", [
            quick_reply('✨ Mehr Sportler', {KEY_SUB: True,
                                            Subscription.Target.ATHLETE.value: True,
                                            KEY_ACTION: ACT_SUBSCRIBE}),
            quick_reply('❌ Abmelden', {KEY_SUB: True,
                                       Subscription.Target.ATHLETE.value: True,
                                       KEY_ACTION: ACT_UNSUBSCRIBE}),
        ])


def result_apply(event, payload, **kwargs):
    sender_id = event['sender']['id']
    action = payload[KEY_ACTION]
    filter = payload[KEY_FILTER]

    target = Subscription.Target.SPORT if filter in SUPPORTED_SPORTS \
        else Subscription.Target.ATHLETE
    sub_filter = {TAR_SPORT: filter} if filter in SUPPORTED_SPORTS else {TAR_ATHLETE: filter}

    if action == ACT_SUBSCRIBE:
        Subscription.create(sender_id, target, sub_filter, Subscription.Type.RESULT)
        reply = f"\nWenn du dich für weitere Ergebnis-Dienste anmelden möchtest, " \
                f"schreibe mir einfach z.B. 'Anmelden für " \
                f"{'Biathlon' if filter in SUPPORTED_SPORTS else 'Viktoria Rebensburg'}.'"
        event.send_text("Super! Ich sage dir, sobald es etwas Neues gibt." + reply)
        send_second_level_subs(event)
    elif action == ACT_UNSUBSCRIBE:
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
    state = payload[KEY_STATE]
    subs = Subscription.query(psid=sender_id, type=Subscription.Type.HIGHLIGHT)

    if state == ACT_SUBSCRIBE:
        target = Subscription.Target.HIGHLIGHT
        filter_arg = {}
        filter_arg[TYP_HIGHLIGHT] = 'Highlight'
        type_arg = Subscription.Type.HIGHLIGHT
        Subscription.create(sender_id, target, filter_arg, type_arg)
        event.send_text('#läuft\nIch melde mich während der Olympischen Spiele zweimal täglich mit '
                        'den Highlights aus PyeonChang bei dir.\nKann ich sonst nochwas liefern?')
        send_first_level_subs(event)
    elif state == ACT_UNSUBSCRIBE:
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
                                                                 {KEY_TARGET: TAR_HIGHLIGHT,
                                                                  KEY_STATE: ACT_UNSUBSCRIBE})
    else:
        highlight_emoji, highlight_button = '❌', button_postback('📝 Anmelden',
                                                                 {KEY_TARGET: TAR_HIGHLIGHT,
                                                                  KEY_STATE: ACT_SUBSCRIBE})

    if any(sub.type is Subscription.Type.RESULT for sub in subs):
        result_button = button_postback('🔧 An-/Abmelden', {KEY_TYPE: KEY_RESULT})
        result_emoji = '✔'
    else:
        result_button = button_postback('📝 Anmelden', {KEY_TYPE: KEY_RESULT})
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


handlers = [
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe', follow_up=True),
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe'),
    ApiAiHandler(api_subscribe, 'push.subscription.unsubscribe'),
    PayloadHandler(livestream_apply,
                   ['sub', Subscription.Type.LIVESTREAM.value, KEY_FILTER, KEY_ACTION]),
    PayloadHandler(livestream_change, ['sub', Subscription.Type.LIVESTREAM.value, KEY_ACTION]),
    PayloadHandler(result_apply, ['sub', Subscription.Type.RESULT.value, KEY_FILTER, KEY_ACTION]),
    PayloadHandler(sport_change, ['sub', Subscription.Target.SPORT.value, KEY_ACTION]),
    PayloadHandler(athlete_change, ['sub', Subscription.Target.ATHLETE.value, KEY_ACTION]),
    PayloadHandler(medal_apply, ['sub', Subscription.Type.MEDAL.value, KEY_FILTER, KEY_ACTION]),
    PayloadHandler(medal_change, ['sub', Subscription.Type.MEDAL.value, KEY_ACTION]),
    PayloadHandler(highlight_change, [KEY_TARGET, KEY_STATE]),
    PayloadHandler(send_second_level_subs, [KEY_TYPE]),
    PayloadHandler(pld_subscriptions, ['send_subscriptions']),
]
