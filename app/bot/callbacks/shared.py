
import logging
import random
import re

from backend.models import Push, Report, FacebookUser
from django.utils import timezone

from feeds.models.subscription import Subscription
from lib.facebook import guess_attachment_type
from lib.response import (quick_reply, button_postback)

logger = logging.getLogger(__name__)

FIRST_REPORT_BTN = [
    'Dann erzähl mal',
    "Los geht's",
    'Lass hören',
]

NEXT_REPORT_BTN = [
    'Und sonst so?',
    'Hast du noch was?',
    'War noch was?',
]

SKIP_REPORT_BTN = [
    'Nächstes Thema',
    'Ist mir egal',
    'Zeig mir was anderes',
]


def get_pushes_by_date(date):
    logger.debug('date: ' + str(date) + ' type of date: ' + str(type(date)))
    pushes = Push.objects.filter(
        pub_date__date=date,
        published=True)

    return pushes


def get_push(force_latest=False):
    now = timezone.localtime()
    date = now.date()
    time = now.time()

    try:
        if force_latest:
            return Push.objects.filter(
                pub_date__lte=now,
                published=True,
            ).latest('pub_date')
        else:
            return Push.objects.filter(
                pub_date__lte=now,
                published=True,
                delivered=False,
                pub_date__date=date,
                pub_date__time__hour=time.hour,
                pub_date__time__minute=time.minute,
            ).latest('pub_date')

    except Push.DoesNotExist:
        return None


def get_latest_report(sport=None, discipline=None):

    try:
        reports = Report.objects.filter(
            published=True,
        )

        if sport:  # TODO: dialogflow intent passes empty sport
            reports = reports.filter(sport=sport)

        if discipline:
            reports = reports.filter(discipline=discipline)

        return reports.latest('created')

    except Report.DoesNotExist:
        return None


def schema(push, event):
    if push.reports.count():
        quick_replies = [
            quick_reply(
                random.choice(FIRST_REPORT_BTN),
                {'push': push.id, 'report': 0, 'next_state': 'intro'})
        ]
    else:
        quick_replies = None

    event.send_text(push.text, quick_replies=quick_replies)


def send_push(event, push, report_nr, state):
    user_id = event['sender']['id']
    media = ''
    url = ''
    next_state = None
    next_report_nr = None
    show_skip = False
    button_title = ''

    if report_nr is not None:
        reports = push.reports.all()
        report = reports[report_nr]
    else:
        reports = None
        report = None

    # Push Intro
    if not report:
        reply = push.text

        if push.reports.count():
            next_state = 'intro'
            # button_title = push.reports.all()[0].headline
            button_title = random.choice(FIRST_REPORT_BTN)
            next_report_nr = 0
        else:
            show_skip = False

    # Report Intro
    elif state == 'intro':
        reply = report.text
        next_report_nr = report_nr
        show_skip = True

        if report.fragments.count():
            next_state = 0
            button_title = report.fragments.order_by('id')[0].question
        else:
            button_title = random.choice(NEXT_REPORT_BTN)
            next_state = 'intro'
            next_report_nr = report_nr + 1
            show_skip = False

        if report.attachment_id:
            media = report.attachment_id
            url = report.media

    # Report Fragment
    elif report.fragments.count() > state:
        fragments = report.fragments.order_by('id')
        fragment = fragments[state]
        reply = fragment.text
        show_skip = True

        # Not last fragment
        if report.fragments.count() - 1 > state:
            next_state = state + 1
            button_title = fragments[next_state].question
            next_report_nr = report_nr

        # Last fragment, but not last Report
        elif push.reports.count() - 1 > report_nr:
            next_state = 'intro'
            next_report_nr = report_nr + 1
            # button_title = reports[next_report_nr].headline
            button_title = random.choice(NEXT_REPORT_BTN)
            show_skip = False

        if fragment.attachment_id:
            media = fragment.attachment_id
            url = fragment.media

    else:
        reply = "Tut mir Leid, dieser Button funktioniert leider nicht."

    # Last Report
    if push.reports.count() - 1 == report_nr:
        show_skip = False

    more_button = quick_reply(
        button_title,
        {'push': push.id, 'report': next_report_nr, 'next_state': next_state}
    )

    skip_button = quick_reply(
        random.choice(SKIP_REPORT_BTN),
        {'push': push.id, 'report': report_nr or 0 + 1, 'next_state': 'intro'}
    )

    if media:
        event.send_attachment_by_id(str(media), guess_attachment_type(str(url)))

    quick_replies = []

    if next_state is not None:
        quick_replies.append(more_button)

    if show_skip:
        quick_replies.append(skip_button)

    reply_split = [s for s in re.split(r"(\r|\n|(\r\n)){2}", reply) if s and s.strip()]

    for i, r in enumerate(reply_split):
        if len(reply_split) - 1 == i:
            quick_replies = [more_button]
            event.send_text(r, quick_replies=quick_replies)
        else:
            event.send_text(r)

    if next_state is None:
        user_subs = Subscription.query(type=Subscription.Type.HIGHLIGHT,
                                       target=Subscription.Target.HIGHLIGHT,
                                       psid=user_id)
        if not user_subs:
            event.send_buttons('Du bist noch nicht für die täglichen Nachrichten angemeldet. '
                               'Möchtest du das jetzt nachholen?',
                               buttons=[button_postback('Ja, bitte!', ['subscribe'])])


def send_report(event, report, state):
    user_id = event['sender']['id']
    reply = ''
    media = ''
    url = ''
    button_title = ''
    next_state = None

    if state == 'intro':
        reply = report.text

        if report.fragments.count():
            next_state = 0
            button_title = report.fragments.order_by('id')[0].question

        if report.attachment_id:
            media = report.attachment_id
            url = report.media

    elif report.fragments.count() > state:
        fragments = report.fragments.order_by('id')
        fragment = fragments[state]
        reply = fragment.text

        if report.fragments.count() - 1 > state:
            next_state = state + 1
            button_title = fragments[next_state].question

        if fragment.attachment_id:
            media = fragment.attachment_id
            url = fragment.media

    else:
        reply = "Tut mir Leid, dieser Button funktioniert leider nicht."

    more_button = quick_reply(
        button_title, {'report': report.id, 'next_state': next_state}
    )

    if media:
        event.send_attachment_by_id(str(media), guess_attachment_type(str(url)))

    reply_split = [s for s in re.split(r"(\r|\n|(\r\n)){2}", reply) if s and s.strip()]

    for i, r in enumerate(reply_split):
        if next_state is not None and len(reply_split) - 1 == i:
            quick_replies = [more_button]
            event.send_text(r, quick_replies=quick_replies)

        else:
            event.send_text(r)
