
import logging
import datetime

from fuzzywuzzy import fuzz, process
from django.utils import timezone

from backend.models import FacebookUser, Wiki, Push, Info
from ..fb import (send_buttons, button_postback, send_text, send_attachment_by_id,
                  guess_attachment_type)
from .shared import get_pushes, schema, send_push, get_pushes_by_date

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

def push(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    date = parameters and parameters.get('date')

    if not date:
        data = get_pushes(force_latest=True)
        schema(data, sender_id)

    else:
        if len(date) == 1:
            find_date = datetime.datetime.strptime(date[0], '%Y-%m-%d').date()
            data = get_pushes_by_date(find_date)

        if len(data) == 0:
            reply = 'Für dieses Datum liegen mir keine Nachrichten vor. ' \
                    'Wähle ein Datum, welches zwischen dem XX.XX.2018 und heute liegt.'
            send_text(sender_id, reply)
        else:
            schema(data, sender_id)


def push_step(event, payload, **kwargs):
    sender_id = event['sender']['id']
    push_id = payload['push']
    next_state = payload['next_state']

    push_ = Push.objects.get(id=push_id)
    send_push(sender_id, push_, state=next_state)


def subscribe(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        reply = "Du bist bereits für Push-Nachrichten angemeldet."
        send_text(user_id, reply)

    else:
        now = timezone.localtime(timezone.now())
        date = now.date()
        time = now.time()

        if time.hour < 18:
            last_push = Push.objects.filter(
                published=True).exclude(pub_date__date__gte=date).latest('pub_date')
        else:
            last_push = Push.objects.filter(
                published=True).exclude(pub_date__date__gt=date).latest('pub_date')

        FacebookUser.objects.create(uid=user_id)
        logger.debug('subscribed user with ID ' + str(FacebookUser.objects.latest('add_date')))
        reply = """
Danke für deine Anmeldung! Du erhältst nun täglich um 18 Uhr dein Update.
Möchtest du jetzt das aktuellste Update aufrufen, klicke auf \'Aktuelle Nachricht\'.
Wenn du irgendwann genug Informationen hast, kannst du dich über das Menü natürlich jederzeit
wieder abmeden."""
        send_buttons(user_id, reply,
                     buttons=[
                        button_postback('Aktuelle Nachricht',
                                        {'push': last_push.id, 'next_state': 'intro'}),
                     ])


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
