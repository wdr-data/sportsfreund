
import logging

from django.utils import timezone

from backend.models import Push, FacebookUser
from ..fb import (send_text, send_attachment_by_id, guess_attachment_type, quick_reply,
                  send_buttons, button_postback)

logger = logging.getLogger(__name__)


def get_pushes_by_date(date):
    logger.debug('date: ' + str(date) + ' type of date: ' + str(type(date)))
    pushes = Push.objects.filter(
        pub_date__date=date,
        published=True)

    return pushes


def get_push():
    now = timezone.localtime()

    try:
        return Push.objects.filter(
            pub_date__lte=now,
            published=True,
            delivered=False
        ).latest('pub_date')

    except Push.DoesNotExist:
        return None


def schema(push, user_id):
    button = quick_reply("Los geht's", {'push': push.id, 'report': None, 'next_state': 'intro'})

    send_text(user_id, push.text, quick_replies=[button])


def send_push(user_id, push, report_nr, state):
    reply = ''
    media = ''
    media_note = ''
    url = ''
    button_title = ''
    next_state = None
    next_report_nr = None

    if report_nr is not None:
        report = push.reports.all()[report_nr]
    else:
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
            media_note = report.media_note

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
            button_title = 'Nächste Meldung'
            next_report_nr = report_nr + 1

        if fragment.attachment_id:
            media = fragment.attachment_id
            url = fragment.media
            media_note = fragment.media_note

    else:
        reply = "Tut mir Leid, dieser Button funktioniert leider nicht."

    more_button = quick_reply(
        button_title, {'push': push.id, 'report': next_report_nr, 'next_state': next_state}
    )

    if media:
        send_attachment_by_id(user_id, str(media), guess_attachment_type(str(url)))
        if media_note:
            send_text(user_id, media_note)

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

        # send_text(user_id, 'Das wars für heute!')
        '''
        if not data.breaking:
            media = '327361671016000'
            send_attachment_by_id(user_id, media, 'image')
        '''
