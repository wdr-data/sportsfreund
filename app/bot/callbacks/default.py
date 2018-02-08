
import datetime
import logging
from time import sleep

from backend.models import FacebookUser, Wiki, Push, Report, Info, Story
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from fuzzywuzzy import fuzz, process

from .subscription import send_subscriptions
from lib.facebook import guess_attachment_type
from lib.response import (button_postback, quick_reply, generic_element,
                          button_web_url, button_share)
from .shared import get_push, schema, send_push, get_pushes_by_date, get_latest_report, send_report

logger = logging.getLogger(__name__)


def greetings(event, **kwargs):
    infos = Info.objects.all().order_by('-id')[:1]

    if infos:
        info = infos[0]
        reply = ("Hallo, hier die neueste Meldung. \n\n"
                 + info.content)

        if info.attachment_id:
            event.send_attachment_by_id(
                info.attachment_id,
                guess_attachment_type(str(info.media))
            )

    else:
        reply = event['message']['nlp']['result']['fulfillment']['speech']

    event.send_text(reply)

def countdown(event, **kwargs):
    today = datetime.datetime.today()
    olympia_start = datetime.datetime(2018, 2, 9, 12)
    delta = olympia_start - today

    reply = 'Die Olympischen Winterspiele starten am 9. Februar 2018 um 20:00 Uhr KST, d.h. um 12:00 Uhr unserer Zeit. ' \
    'Bis dahin sind es noch {days} Tage, {hours} Stunden und {minutes} Minuten.'.format(
            days=delta.days,
            hours=delta.seconds//3600,
            minutes=(delta.seconds%3600)//60
        )
    event.send_text(reply)

def korea_standard_time(event, **kwargs):
    kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)

    reply = 'In Pyeongchang, dem Austragungsort der Olympischen Winterspiele, ist es {time} Uhr KST.'.format(
        time = datetime.datetime.strftime(kst, '%H:%M')
        )
    event.send_text(reply)

def get_started(event, **kwargs):
    story(event, slug='onboarding', fragment_nr=None, subscribe=True)


def share_bot(event, **kwargs):
    reply = "Teile den Sportsfreund mit deinen Freunden!"

    title = "Der Sportsfreund ist ein Facebook Messenger Dienst der Sportschau"
    subtitle = "Befrage den Messenger über die Olympischen Winterspiele 2018."
    #image_url = ""
    shared_content = [generic_element(title, subtitle, buttons = [button_web_url("Schreibe dem Sportsfreund", "https://www.m.me/sportsfreund.sportschau")])]
    message = generic_element("Teile den Sportsfreund mit deinen Freunden!", buttons = [button_share(shared_content)])

    event.send_generic(elements=[message])


def privacy(event, **kwargs):
    story(event, slug='datenschutz', fragment_nr=None)


def how_to(event, **kwargs):
    story(event, slug='wie-funktionierst-du', fragment_nr=None)


def about_bot(event, **kwargs):
    story(event, slug='sportsfreund', fragment_nr=None)


def company_details(event, **kwargs):
    story(event, slug='impressum', fragment_nr=None)


def push(event, parameters, **kwargs):
    date = parameters and parameters.get('date')

    if not date:
        push = get_push(force_latest=True)
        if push:
            event.send_text(f"Hier die Highlights vom"
                            f" {push.pub_date.strftime('%d.%m.%Y %H:%M')}Uhr:")
            send_push(event, push=push, report_nr=None, state=None)
        else:
            reply = 'Keine Highlights gefunden.'
            event.send_text(reply)

    else:
        if len(date) == 1:
            find_date = datetime.datetime.strptime(date[0], '%Y-%m-%d').date()
            pushes = get_pushes_by_date(find_date)

        if len(pushes) == 0:
            reply = 'Für dieses Datum liegen mir keine Nachrichten vor. ' \
                    'Wähle ein Datum, welches zwischen dem XX.XX.2018 und heute liegt.'
            event.send_text(reply)

        else:
            schema(pushes[-1], event)


def push_step(event, payload, **kwargs):
    push_id = payload['push']
    report_nr = payload['report']
    next_state = payload['next_state']

    push = Push.objects.get(id=push_id)

    send_push(event, push, report_nr, next_state)


def report(event, parameters, **kwargs):
    sport = parameters and parameters.get('sport')
    discipline = parameters and parameters.get('discipline')

    report = get_latest_report(sport=sport, discipline=discipline)

    if report:
        send_report(event, report, 'intro')
    else:
        reply = 'Keine Meldung gefunden.'
        event.send_text(reply)


def report_step(event, payload, **kwargs):
    report_id = payload['report']
    next_state = payload['next_state']

    report = Report.objects.get(id=report_id)

    send_report(event, report, next_state)


def subscribe(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        reply = "Du bist bereits für Push-Nachrichten angemeldet."
        event.send_text(reply)

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
Das hat geklappt. Du bist jetzt für die Ski-Alpin und Biathlon News angemeldet. Du kannst dich über das Menü wieder abmelden."""

        if buttons:
            event.send_buttons(reply, buttons=buttons)
        else:
            event.send_text(reply)


def unsubscribe(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        logger.debug('deleted user with ID: ' + str(FacebookUser.objects.get(uid=user_id)))
        FacebookUser.objects.get(uid=user_id).delete()
        event.send_text("Schade, dass du uns verlassen möchtest. Du wurdest aus der Empfängerliste für "
                        "Push Benachrichtigungen gestrichen. "
                        "Wenn du doch nochmal Interesse hast, kannst du mich auch einfach fragen: \n"
                        "z.B. \"Wie war der Push von gestern/ vorgestern/ letztem Sonntag?\"")
    else:
        reply = "Du bist noch kein Nutzer der Push-Nachrichten. Wenn du dich anmelden möchtest, " \
                "wähle \"Anmelden\" über das Menü."
        event.send_text(reply)


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
                event.send_attachment_by_id(
                    str(match.attachment_id),
                    type=guess_attachment_type(str(match.media))
                )
            except:
                logging.exception('Sending attachment failed')

    if reply:
        event.send_text(reply)


def apiai_fulfillment(event, **kwargs):
    fulfillment = event['message']['nlp']['result']['fulfillment']
    if fulfillment['speech']:
        event.send_text(fulfillment['speech'])


def story_payload(event, payload, **kwargs):
    story(event, payload['story'], payload['fragment'])


def story(event, slug, fragment_nr, subscribe=False):
    reply = ''
    media = ''
    url = ''
    button_title = ''
    link_story = None

    try:
        story = Story.objects.get(slug=slug)
    except ObjectDoesNotExist:
        event.send_text('Huppsala, das hat nicht funktioniert :(')

    fragments = story.fragments.order_by('id')

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

    elif story.fragments.count() > fragment_nr:
        reply = fragment.text

        if story.fragments.count() - 1 > fragment_nr:
            next_fragment_nr = fragment_nr + 1
            button_title = fragments[next_fragment_nr].button

        if fragment.attachment_id:
            media = fragment.attachment_id
            url = fragment.media

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
        event.send_attachment_by_id(str(media), guess_attachment_type(str(url)))

    if quick_replies:
        event.send_text(reply, quick_replies=quick_replies)

    else:
        event.send_text(reply)

        if subscribe:
            send_subscriptions(event)
