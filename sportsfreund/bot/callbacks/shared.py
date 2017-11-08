
import logging

from django.utils import timezone

from backend.models import Push, FacebookUser
from ..fb import (send_text, send_attachment_by_id, guess_attachment_type, quick_reply,
                  send_buttons, button_postback)

logger = logging.getLogger(__name__)


def get_pushes(force_latest=False):
    now = timezone.localtime(timezone.now())
    date = now.date()
    time = now.time()

    if time.hour < 18 and not force_latest:
        infos = Push.objects.filter(
            pub_date__date=date,
            pub_date__hour__lt=8,
            published=True,
            breaking=False)

    else:
        infos = Push.objects.filter(
            pub_date__date=date,
            pub_date__hour__gte=8,
            pub_date__hour__lt=20,
            published=True,
            breaking=False)

    return infos


def get_pushes_by_date(date):
    logger.debug('date: ' + str(date) + ' type of date: ' + str(type(date)))
    infos = Push.objects.filter(
        pub_date__date=date,
        pub_date__hour__gte=8,
        pub_date__hour__lt=20,
        published=True,
        breaking=False)

    return infos


def get_breaking():
    now = timezone.localtime(timezone.now())
    date = now.date()
    time = now.time()

    try:
        return Push.objects.get(
            pub_date__date=date,
            pub_date__hour=time.hour,
            pub_date__minute=time.minute,
            published=True,
            breaking=True)

    except Push.DoesNotExist:
        return None


def schema(data, user_id):
    reply = "Hier kommt dein Update"
    send_text(user_id, reply)
    reply = ""
    first_id = None

    for info in data:
        if first_id is None:
            first_id = info.id
        reply += ' +++ ' + info.headline
    reply += ' +++ '

    button = quick_reply("Los geht's", {'push': first_id, 'next_state': 'intro'})
    quick_replies = [button]

    send_text(user_id, reply, quick_replies=quick_replies)


def send_push(user_id, data, state='intro'):
    reply = ''
    media = ''
    media_note = ''
    url = ''
    button_title = ''
    next_state = None

    if state == 'intro':
        reply = data.intro_text

        if data.fragments.count():
            next_state = 0
            button_title = data.fragments[0].question

        if data.attachment_id:
            media = data.attachment_id
            url = data.media
            media_note = data.media_note

    elif data.fragments.count() - 1 > state:
        fragment = data.fragments[state]
        reply = fragment.text

        if data.fragments.count() > state:
            next_state = state + 1
            button_title = fragment.question

        if fragment.attachment_id:
            media = fragment.attachment_id
            url = fragment.media
            media_note = fragment.media_note

    else:
        reply = "Tut mir Leid, dieser Button funktioniert leider nicht."

    more_button = quick_reply(
        button_title, {'push': data.id, 'next_state': next_state}
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
