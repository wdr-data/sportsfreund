
import logging
import datetime

from fuzzywuzzy import fuzz, process
from django.utils import timezone

from backend.models import FacebookUser, Wiki, Push, Info, Story, StoryFragment
from ..fb import (send_buttons, button_postback, send_text, send_attachment_by_id,
                  guess_attachment_type, quick_reply, generic_element, send_generic, button_web_url, button_share)
from .shared import get_push, schema, send_push, get_pushes_by_date

logger = logging.getLogger(__name__)


def greetings(event, **kwargs):
    sender_id = event['sender']['id']
    infos = Info.objects.all().order_by('-id')[:1]

    if infos:
        info = infos[0]
        reply = ("Hallo, hier die neueste Meldung. \n\n"
                 + info.content)

        if info.attachment_id:
            send_attachment_by_id(
                sender_id,
                info.attachment_id,
                guess_attachment_type(str(info.media))
            )

    else:
        reply = event['message']['nlp']['result']['fulfillment']['speech']

    send_text(sender_id, reply)

def countdown(event, **kwargs):
    sender_id = event['sender']['id']
    today = datetime.datetime.today()
    olympia_start = datetime.datetime(2018, 2, 9, 12)
    delta = olympia_start - today

    reply = 'Die Olympischen Winterspiele starten am 9. Februar 2018 um 20:00 Uhr KST, d.h. um 12:00 Uhr unserer Zeit. ' \
    'Bis dahin sind es noch {days} Tage, {hours} Stunden und {minutes} Minuten.'.format(
            days=delta.days,
            hours=delta.seconds//3600,
            minutes=(delta.seconds%3600)//60
        )
    send_text(sender_id, reply)

def korea_standard_time(event, **kwargs):
    sender_id = event['sender']['id']
    kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)

    reply = 'In Pyeongchang, dem Austragungsort der Olympischen Winterspiele, ist es {hours}:{minutes} Uhr KST.'.format(
            hours=kst.hour,
            minutes=kst.minute
        )
    send_text(sender_id, reply)

def get_started(event, **kwargs):
    sender_id = event['sender']['id']
    reply = """
Tach, ich bin Sportsfreund, ein Facebook Messenger Dienst der Sportschau.
Meine Leidenschaft zur Zeit: Wintersport und Daten. Noch bin ich in der Testphase und kenne mich deshalb nur mit Wintersport aus."""
    next_state = 'step_one'

    send_buttons(sender_id, reply,
                 buttons=[
                    button_postback('Fragt mich schlau', {'start_message': next_state}),
                 ])


def start_message(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload.get('start_message')

    if state == 'step_one':
        reply = """
Je mehr Fragen Ihr mir nach Ergebnissen, Sportlern, Live-Streams oder Sportstätten stellt, desto schneller lerne ich dazu.
Schreibt mir dafür einfach eine Nachricht. Mein Ziel: Bei den Olympischen Winterspielen euer Freund und Helfer zu werden - Immer da, wenn Ihr etwas wissen wollt."""
        send_buttons(sender_id, reply,
                     buttons=[
                        button_postback('Highlights als Abo', {'start_message': 'step_two'}),
                     ])
    elif state == 'step_two':
        reply = """
Unten neben der Texteingabe gibt es ein Menü. Da findet Ihr mehr Infos zu mir und meinen Funktionen.
Abonniert meine Highlights und Ihr bekommt - zurzeit noch unregelmäßig - Ergebnisse, Fun-Facts
und die stärksten Geschichten des Wintersports bequem per Messenger Nachricht."""
        send_text(sender_id, reply)

def share_bot(event, **kwargs):
    sender_id = event['sender']['id']
    reply = "Teile den Sportsfreund mit deinen Freunden!"

    title = "Der Sportsfreund ist ein Facebook Messenger Dienst der Sportschau"
    subtitle = "Befrage den Messenger über die Olympischen Winterspiele 2018."
    #image_url = ""
    shared_content = [generic_element(title, subtitle, buttons = [button_web_url("Schreibe dem Sportsfreund", "https://www.m.me/sportsfreund.sportschau")])]
    message = generic_element("Teile den Sportsfreund mit deinen Freunden!", buttons = [button_share(shared_content)])

    send_generic(sender_id,
                elements = [message])

def push(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    date = parameters and parameters.get('date')

    if not date:
        push = get_push(force_latest=True)
        if push:
            schema(push, sender_id)
        else:
            reply = 'Keine Pushes gefunden.'
            send_text(sender_id, reply)

    else:
        if len(date) == 1:
            find_date = datetime.datetime.strptime(date[0], '%Y-%m-%d').date()
            pushes = get_pushes_by_date(find_date)

        if len(pushes) == 0:
            reply = 'Für dieses Datum liegen mir keine Nachrichten vor. ' \
                    'Wähle ein Datum, welches zwischen dem XX.XX.2018 und heute liegt.'
            send_text(sender_id, reply)

        else:
            schema(pushes[-1], sender_id)


def push_step(event, payload, **kwargs):
    sender_id = event['sender']['id']
    push_id = payload['push']
    report_nr = payload['report']
    next_state = payload['next_state']

    push = Push.objects.get(id=push_id)

    send_push(sender_id, push, report_nr, next_state)


def subscribe(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        reply = "Du bist bereits für Push-Nachrichten angemeldet."
        send_text(user_id, reply)

    else:
        now = timezone.localtime(timezone.now())

        try:
            last_push = Push.objects.filter(
                published=True).exclude(pub_date__date__gt=now).latest('pub_date')

            buttons = [
                button_postback('Aktuelle Nachricht',
                                {'push': last_push.id, 'report': None, 'next_state': 'intro'}),
            ]

        except Push.DoesNotExist:
            buttons = None

        FacebookUser.objects.create(uid=user_id)
        logger.debug('subscribed user with ID ' + str(FacebookUser.objects.latest('add_date')))
        reply = """
Danke für deine Anmeldung! Du erhältst nun täglich um 18 Uhr dein Update.
Möchtest du jetzt das aktuellste Update aufrufen, klicke auf \'Aktuelle Nachricht\'.
Wenn du irgendwann genug Informationen hast, kannst du dich über das Menü natürlich jederzeit
wieder abmeden."""

        if buttons:
            send_buttons(user_id, reply, buttons=buttons)
        else:
            send_text(user_id, reply)


def unsubscribe(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        logger.debug('deleted user with ID: ' + str(FacebookUser.objects.get(uid=user_id)))
        FacebookUser.objects.get(uid=user_id).delete()
        send_text(user_id,
                "Schade, dass du uns verlassen möchtest. Du wurdest aus der Empfängerliste für "
                "Push Benachrichtigungen gestrichen. "
                "Wenn du doch nochmal Interesse hast, kannst du mich auch einfach fragen: \n"
                "z.B. \"Wie war der Push von gestern/ vorgestern/ letztem Sonntag?\""
        )
    else:
        reply = "Du bist noch kein Nutzer der Push-Nachrichten. Wenn du dich anmelden möchtest, " \
                "wähle \"Anmelden\" über das Menü."
        send_text(user_id, reply)


def wiki(event, parameters, **kwargs):
    user_id = event['sender']['id']
    text = parameters.get('wiki')

    wikis = Wiki.objects.all()
    best_match = process.extractOne(
        text,
        wikis,
        scorer=fuzz.token_set_ratio,
        score_cutoff=90)

    if not best_match:
        reply = "Tut mir Leid, darauf habe noch ich keine Antwort. Frag mich die Tage nochmal."
    else:
        match = best_match[0]
        if match.output == 'empty':
            reply = "Moment, das muss ich nachschauen. " \
                    "Eine Antwort habe ich bald.".format(word=text)
        else:
            reply = match.output

        if match.attachment_id:
            try:
                send_attachment_by_id(
                    user_id,
                    str(match.attachment_id),
                    type=guess_attachment_type(str(match.media))
                )
            except:
                logging.exception('Sending attachment failed')

    if reply:
        send_text(user_id, reply)


def apiai_fulfillment(event, **kwargs):
    sender_id = event['sender']['id']

    fulfillment = event['message']['nlp']['result']['fulfillment']
    if fulfillment['speech']:
        send_text(sender_id, fulfillment['speech'])


def story_payload(event, payload, **kwargs):
    story(event, payload['story'], payload['fragment'])


def story(event, slug, fragment_nr):
    user_id = event['sender']['id']

    reply = ''
    media = ''
    media_note = ''
    url = ''
    button_title = ''
    link_story = None

    story = Story.objects.get(slug=slug)
    fragments = story.fragments.all()

    next_fragment_nr = None

    if fragment_nr is not None:
        fragment = fragments[fragment_nr]
    else:
        fragment = None

    if not fragment:
        reply = story.text

        if story.fragments.count():
            next_fragment_nr = 0
            button_title = fragments[next_fragment_nr].button

        if story.attachment_id:
            media = story.attachment_id
            url = story.media
            media_note = story.media_note

    elif story.fragments.count() > fragment_nr:
        reply = fragment.text

        if story.fragments.count() - 1 > fragment_nr:
            next_fragment_nr = fragment_nr + 1
            button_title = fragments[next_fragment_nr].button

        if fragment.attachment_id:
            media = fragment.attachment_id
            url = fragment.media
            media_note = fragment.media_note

        link_story = fragment.link_story

    else:
        reply = "Tut mir Leid, dieser Button funktioniert leider nicht."

    if next_fragment_nr is not None:
        more_button = quick_reply(
            button_title, {'story': story.slug, 'fragment': next_fragment_nr}
        )

        quick_replies = [more_button]
    else:
        quick_replies = []

    if link_story:
        quick_replies.append(
            quick_reply(
                link_story.name, {'story': link_story.slug, 'fragment': None}
            )
        )

    if media:
        send_attachment_by_id(user_id, str(media), guess_attachment_type(str(url)))
        if media_note:
            send_text(user_id, media_note)

    if quick_replies:
        send_text(user_id, reply, quick_replies=quick_replies)

    else:
        send_text(user_id, reply)
