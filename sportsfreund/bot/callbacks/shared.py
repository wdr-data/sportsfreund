
import logging

from django.utils import timezone

from backend.models import Push, Report, FacebookUser
from ..fb import (send_text, send_attachment_by_id, guess_attachment_type, quick_reply,
                  send_buttons, button_postback)

logger = logging.getLogger(__name__)


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

        if sport is not None:
            reports = reports.filter(sport=sport)

        if discipline is not None:
            reports = reports.filter(discipline=discipline)

        return reports.latest('created')

    except Report.DoesNotExist:
        return None


def schema(push, user_id):
    if push.reports.count():
        quick_replies = [
            quick_reply("Los geht's", {'push': push.id, 'report': 0, 'next_state': 'intro'})
        ]
    else:
        quick_replies = None

    send_text(user_id, push.text, quick_replies=quick_replies)


def send_push(user_id, push, report_nr, state):
    reply = ''
    media = ''
    url = ''
    button_title = ''
    next_state = None
    next_report_nr = None

    if report_nr is not None:
        reports = push.reports.all()
        report = reports[report_nr]
    else:
        reports = None
        report = None

    if not report:
        reply = push.text

        if push.reports.count():
            next_state = 'intro'
            button_title = push.reports.all()[0].headline
            next_report_nr = 0

    elif state == 'intro':
        reply = report.text
        next_report_nr = report_nr

        if report.fragments.count():
            next_state = 0
            button_title = report.fragments.all()[0].question

        if report.attachment_id:
            media = report.attachment_id
            url = report.media

    elif report.fragments.count() > state:
        fragments = report.fragments.all()
        fragment = fragments[state]
        reply = fragment.text

        if report.fragments.count() - 1 > state:
            next_state = state + 1
            button_title = fragments[next_state].question
            next_report_nr = report_nr

        elif push.reports.count() - 1 > report_nr:
            next_state = 'intro'
            next_report_nr = report_nr + 1
            button_title = reports[next_report_nr].headline

        if fragment.attachment_id:
            media = fragment.attachment_id
            url = fragment.media

    else:
        reply = "Tut mir Leid, dieser Button funktioniert leider nicht."

    more_button = quick_reply(
        button_title, {'push': push.id, 'report': next_report_nr, 'next_state': next_state}
    )

    if media:
        send_attachment_by_id(user_id, str(media), guess_attachment_type(str(url)))

    if next_state is not None:
        quick_replies = [more_button]
        send_text(user_id, reply, quick_replies=quick_replies)

    else:
        send_text(user_id, reply)

        try:
            FacebookUser.objects.get(uid=user_id)
        except FacebookUser.DoesNotExist:
            send_buttons(user_id, 'Du bist noch nicht für die täglichen Nachrichten angemeldet. '
                                  'Möchtest du das jetzt nachholen?',
                         buttons=[button_postback('Ja, bitte!', ['subscribe'])])


def send_report(user_id, report, state):
    reply = ''
    media = ''
    url = ''
    button_title = ''
    next_state = None

    if state == 'intro':
        reply = report.text

        if report.fragments.count():
            next_state = 0
            button_title = report.fragments.all()[0].question

        if report.attachment_id:
            media = report.attachment_id
            url = report.media

    elif report.fragments.count() > state:
        fragments = report.fragments.all()
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
        send_attachment_by_id(user_id, str(media), guess_attachment_type(str(url)))

    if next_state is not None:
        quick_replies = [more_button]
        send_text(user_id, reply, quick_replies=quick_replies)

    else:
        send_text(user_id, reply)
