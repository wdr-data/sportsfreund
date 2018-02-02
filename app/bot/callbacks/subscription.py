import random

from bson.objectid import ObjectId

from feeds.config import supported_sports
from feeds.models.person import Person
from feeds.models.subscription import Subscription
from lib.response import list_element, button_postback, quick_reply
from ..handlers.apiaihandler import ApiAiHandler
from ..handlers.payloadhandler import PayloadHandler
from feeds.config import GERMAN_ATHLETES_OLYMPIA

GLOBES = ('🌎', '🌏', '🌍')


def api_subscribe(event, parameters, **kwargs):
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')
    first_name = parameters.get('first_name')
    last_name = parameters.get('last_name')
    country = parameters.get('country')
    subscription_type = parameters.get('subscription_type')
    athlete = None

    if last_name and first_name:

        german_athlete_names = set((athlete.first_name, athlete.last_name)
                                   for athlete in GERMAN_ATHLETES_OLYMPIA)

        if (first_name, last_name) not in german_athlete_names:
            if not Person.query(firstname=first_name, surname=last_name):
                event.send_text('Diese Person ist leider noch nicht in meiner Datenbank... '
                                'Bist du sicher, dass du dich nicht vertippt hast?')
                return

        athlete = ' '.join([first_name, last_name])

    highlight = subscription_type == 'highlight' or parameters.get('highlight')
    medal = subscription_type == 'medal'

    if highlight:
        payload = {'target': 'highlight', 'state': 'subscribe'}
        highlight_subscriptions(event, payload)
        return
    if medal and country:
        payload = {'target': 'medal', 'state': 'subscribe', 'country': country}
        medal_subscriptions(event, payload)
        return
    elif medal and not country:
        event.send_text('Sehr gerne trage ich dich für die Medaillen-Benachrichtigungen '
                        'ein. Sag mir doch bitte noch, welches Land dich interessiert '
                        f'{random.choice(GLOBES)}')
        return
    elif not sport and not first_name and not last_name and not highlight:
        subs = Subscription.query(psid=event['sender']['id'])
        add = 'Du bist noch für keinen Nachrichten-Service angemeldet. ' if not subs \
            else 'Dies ist die Übersicht deiner angemeldeten Services. '
        event.send_text(f'{add}Du kannst diese jederzeit ändern.')
        send_subscriptions(event)
        return
    elif (last_name and not first_name) or (first_name and not last_name):
        event.send_text('Wenn du dich für die Ergebnisse eines Athleten anmelden möchtest, '
                        'schicke mir den Vor- und Nachnamen. Nur um Verwechslungen zu vermeiden ;)')
        return

    subscribe_flow(event, sport, discipline, athlete)


def subscribe_flow(event, sport=None, discipline=None, athlete=None):
    sender_id = event['sender']['id']
    filter_arg = {}

    target = Subscription.Target.SPORT if sport else (
        Subscription.Target.DISCIPLINE if discipline else Subscription.Target.ATHLETE)

    if sport:
        filter_arg['sport'] = sport
    elif discipline:
        filter_arg['sport'] = sport
        filter_arg['discipline'] = discipline
    elif athlete:
        filter_arg['athlete'] = athlete

    type_arg = Subscription.Type.RESULT

    Subscription.create(sender_id, target, filter_arg, type_arg)

    event.send_text('Vielen Dank für deine Anmeldung. In folgender Liste siehst du alle Themen, '
              'über die ich dich automatisch informiere. Du kannst sie jederzeit ändern.')
    result_medal_subscriptions(event)


def api_unsubscribe(event, parameters, **kwargs):
    unsubscribe_flow(event)


def unsubscribe_flow(event):
    subs = Subscription.query(psid=event['sender']['id'])
    reply = f'Du bist noch für keinen Nachrichten-Service angemeldet. Falls du dich anmelden ' \
          f'möchtest, kannst du das hier tun.' if not subs \
        else f'Du möchtest dich von automatischen Nachrichten abmelden - OK. ' \
             f'In der Liste siehst du alle deine Anmeldungen. ' \
             f'Du kannst Sie jederzeit über die Buttons ändern.'
    event.send_text(reply)
    send_subscriptions(event)


def pld_subscriptions(event, payload, **kwargs):
    send_subscriptions(event)


def send_subscriptions(event, **kwargs):
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
    ]

    event.send_list(elements)


def highlight_subscriptions(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['state']
    subs = Subscription.query(psid=sender_id)

    if state == 'subscribe':
        target = Subscription.Target.HIGHLIGHT
        filter_arg = {}
        filter_arg['highlight'] = 'Highlight'
        type_arg = Subscription.Type.HIGHLIGHT
        Subscription.create(sender_id, target, filter_arg, type_arg)
        event.send_text('#läuft\nIch melde mich während der Olympischen Spiele zweimal täglich mit den '
                        'Highlights aus PyeonChang bei dir.\nKann ich sonst nochwas liefern?')
        send_subscriptions(event)
    elif state == 'unsubscribe':
        for sub in subs:
            if sub.target is Subscription.Target.HIGHLIGHT:
                event.send_text('Du bist nun von den Highlights abgemeldet. Du kannst das '
                                'jederzeit wieder ändern.')
                unsubscribe(event, {'unsubscribe': str(sub._id)})


def medal_subscriptions(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['state']
    country = payload['country']
    subs = Subscription.query(psid=sender_id)

    if state == 'subscribe':
        target = Subscription.Target.COUNTRY
        filter_arg = {'country': country}
        type_arg = Subscription.Type.MEDAL
        Subscription.create(sender_id, target, filter_arg, type_arg)
        event.send_text(f'Cool! Wann immer {country} eine Olympische Medaille erkämpft, sage ich '
                        'dir Bescheid!')
        send_subscriptions(event)

    elif state == 'unsubscribe':
        for sub in subs:
            if sub.target is Subscription.Target.COUNTRY:
                event.send_text(f'Du bekommst ab jetzt keine Benachrichtigungen über Medaillen '
                                f'des Landes "{country}"')
                unsubscribe(event, {'unsubscribe': str(sub._id)})


def result_medal_subscriptions(event, **kwargs):
    sender_id = event['sender']['id']
    subs = (Subscription.query(type=Subscription.Type.RESULT, psid=sender_id) +
            Subscription.query(type=Subscription.Type.MEDAL, psid=sender_id))

    if any(sub.target is Subscription.Target.SPORT for sub in subs):
        sport_subtitle = ', '.join(
            [str(Subscription.describe_filter(sub.filter))
             for sub in subs if sub.target is Subscription.Target.SPORT])

        if len(sport_subtitle) > 80:
            sport_subtitle = sport_subtitle[:77] + '...'
        sport_emoji = '✔'
        sport_button = button_postback('🔧 An-/Abmelden',
                                       {'target': 'sport', 'filter': None, 'option': None})
    else:
        sport_subtitle = 'Nicht angemeldet'
        sport_emoji = '❌'
        sport_button = button_postback('📝 Anmelden',
                                       {'target': 'sport', 'filter': None, 'option': 'subscribe'})

    if any(sub.target is Subscription.Target.ATHLETE for sub in subs):
        athlete_subtitle = ', '.join(
            [str(Subscription.describe_filter(sub.filter))
             for sub in subs if sub.target is Subscription.Target.ATHLETE])

        if len(athlete_subtitle) > 80:
            athlete_subtitle = athlete_subtitle[:77] + '...'
        athlete_emoji = '✔'
        athlete_button = button_postback('🔧 An-/Abmelden',
                                         {'target': 'athlete', 'filter': None, 'option': None})
    else:
        athlete_subtitle = 'Nicht angemeldet'
        athlete_emoji = '❌'
        athlete_button = button_postback(
            '📝 Anmelden', {'target': 'athlete', 'filter': None, 'option': 'subscribe'})

    if any(sub.target is Subscription.Target.COUNTRY for sub in subs):
        country_subtitle = ', '.join(
            [str(Subscription.describe_filter(sub.filter))
             for sub in subs if sub.target is Subscription.Target.COUNTRY])

        if len(country_subtitle) > 80:
            country_subtitle = country_subtitle[:77] + '...'

        country_emoji = '✔'
        country_button = button_postback('🔧 An-/Abmelden',
                                         {'target': 'country', 'filter': None, 'option': None})
    else:
        country_subtitle = 'Nicht angemeldet'
        country_emoji = '❌'
        country_button = button_postback(
            '📝 Anmelden', {'target': 'country', 'filter': None, 'option': 'subscribe'})

    elements = [
        list_element(
            'Sportart ' + sport_emoji,
            sport_subtitle,
            buttons=[sport_button]),
        list_element(
            'Sportler ' + athlete_emoji,
            athlete_subtitle,
            buttons=[athlete_button]),
        list_element(
            'Medaillen ' + country_emoji,
            country_subtitle,
            buttons=[country_button]),
    ]

    event.send_list(elements)


def result_medal_change(event, payload, **kwargs):
    sender_id = event['sender']['id']
    option = payload['option']
    target = payload['target']
    filter_arg = payload['filter']
    subs = (Subscription.query(type=Subscription.Type.RESULT, psid=sender_id) +
            Subscription.query(type=Subscription.Type.MEDAL, psid=sender_id))

    if option == 'unsubscribe':
        if not filter_arg:
            if len(subs) > 1:
                if target == 'sport':
                    filter_list = [Subscription.describe_filter(sub.filter)
                         for sub in subs if sub.target is Subscription.Target.SPORT]
                elif target == 'athlete':
                    filter_list = [Subscription.describe_filter(sub.filter)
                         for sub in subs if sub.target is Subscription.Target.ATHLETE]
                elif target == 'country':
                    filter_list = [Subscription.describe_filter(sub.filter)
                         for sub in subs if sub.target is Subscription.Target.COUNTRY]

                quickreplies = [
                    quick_reply(filter,
                                {'target': target, 'filter': filter, 'option': 'unsubscribe'})
                    for filter in filter_list[:11]
                ]

                event.send_text(
                    'Für welchen Dienst möchtest du dich abmelden?',
                    quickreplies
                )
            elif len(subs) == 1:
                event.send_buttons(f'Du bist für den Ergebnis Dienst zu '
                                   f'{Subscription.describe_filter(subs[0].filter)} angemeldet. '
                                   f'Möchtest du dich abmelden?',
                                   buttons=[button_postback('Abmelden',
                                                            {'unsubscribe': str(subs[0]._id)})])
        else:
            for sub in subs:
                if Subscription.describe_filter(sub.filter) == filter_arg:
                    unsubscribe(event, {'unsubscribe': str(sub._id)})
                    event.send_text(f'Okidoki. Du bekommst keine {filter_arg}-Ergebnisse mehr.')
    elif option == 'subscribe':
        if not filter_arg:
            if target == 'sport':
                filter_list = [Subscription.describe_filter(sub.filter)
                               for sub in subs if sub.target is Subscription.Target.SPORT]
                sports = [sport for sport in supported_sports if sport not in filter_list]
                if not sports:
                    event.send_text(f'Du bist bereits für alle möglichen Sportarten '
                                               f'angemeldet. Du scheinst ja genau so ein '
                                               f'Wintersport Nerd zu sein wie ich 🤓')
                else:
                    quickreplies = [quick_reply(sport, {'target': target,
                                                        'filter': sport,
                                                        'option': 'subscribe'})
                                    for sport in sports[:11]]
                    event.send_text(f'Für welche Sportart soll ich dir die Ergebnisse schicken? ',
                                    quickreplies)
            elif target == 'country':
                event.send_text('Du kannst dich ganz einfach für die Medaillen-Benachrichtigungen '
                                f'anmelden {random.choice(GLOBES)} Dafür musst du mir z. B. '
                                'folgendes schreiben:\n\n'
                                '"Anmelden für Medaillen von Deutschland"')
            else:
                event.send_text(f'Über wen soll ich dich informieren? Schreibe mir zum Beispiel '
                                f'"Viktoria Rebensburg" - bitte nenne immer den Vor- und Nachnamen,'
                                f' damit es keine Missverständnisse gibt.')

        else:
            sub_target = Subscription.Target(target)

            sub_filter = {}
            if target == 'sport':
                sub_filter['sport'] = filter_arg
                reply = f'Ok. In der Übersicht siehst du für welche Ergebnis-Dienste du ' \
                        f'angemeldet bist.'
            elif target == 'athlete':
                sub_filter['athlete'] = filter_arg
                reply = f'Top. Ich melde mich, wenn es etwas Neues von {filter_arg} gibt.'
            elif target == 'country':
                sub_filter['country'] = filter_arg
                reply = f'Top. Ich melde mich, wenn es neue Medaillen für {filter_arg} gibt.'

            if sub_target in (Subscription.Target.SPORT, Subscription.Target.ATHLETE,
                              Subscription.Target.DISCIPLINE):
                sub_type = Subscription.Type.RESULT
            else:
                sub_type = Subscription.Type.MEDAL

            Subscription.create(sender_id, sub_target, sub_filter, sub_type)
            event.send_text(reply + '\nMöchtest du dich noch für andere Nachrichten anmelden?')
            send_subscriptions(event)
    else:
        event.send_buttons('Was möchtest du machen?',
                           buttons=[
                               button_postback(
                                   'Anmelden',
                                   {'target': target, 'filter': None, 'option': 'subscribe'}),
                               button_postback(
                                   'Abmelden',
                                   {'target': target, 'filter': None, 'option': 'unsubscribe'})])


def unsubscribe(event, payload):
    sub_id = payload['unsubscribe']

    Subscription.delete(_id=ObjectId(sub_id))
    send_subscriptions(event)


def subscribe_menu(event, payload):
    event.send_text('Dies ist die Übersicht deiner angemeldeten Services. '
                         'Du kannst diese jederzeit ändern.')
    send_subscriptions(event)


handlers = [
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe', follow_up=True),
    ApiAiHandler(api_subscribe, 'push.subscription.subscribe'),
    ApiAiHandler(api_subscribe, 'push.subscription.unsubscribe'),
    PayloadHandler(highlight_subscriptions, ['target', 'state']),
    PayloadHandler(result_medal_subscriptions, ['type']),
    PayloadHandler(result_medal_change, ['target', 'filter', 'option']),
    PayloadHandler(unsubscribe, ['unsubscribe']),
    PayloadHandler(subscribe_menu, ['subscribe_menu']),
    PayloadHandler(pld_subscriptions, ['send_subscriptions']),
]
