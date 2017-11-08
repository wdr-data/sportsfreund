import logging
from threading import Thread
from time import sleep
import os
import json

import schedule
#from django.utils.timezone import localtime, now
from apiai import ApiAI

from backend.models import FacebookUser
from .fb import send_text, PAGE_TOKEN
from .handlers.payloadhandler import PayloadHandler
from .handlers.texthandler import TextHandler
from .handlers.apiaihandler import ApiAiHandler
from .callbacks.default import (get_started, start_message, greetings, push, push_step, subscribe, unsubscribe,
                                apiai_fulfillment, wiki)
from .callbacks.shared import get_pushes, schema, send_push, get_breaking

logger = logging.getLogger(__name__)

API_AI_TOKEN = os.environ.get('SPORTSFREUND_API_AI_TOKEN', 'na')

ADMINS = [
]


def make_event_handler():
    ai = ApiAI(API_AI_TOKEN)

    handlers = [
        ApiAiHandler(greetings, 'gruss'),
        PayloadHandler(greetings, ['gruss']),

        PayloadHandler(get_started, ['start']),
        PayloadHandler(start_message, ['start_message']),

        ApiAiHandler(subscribe, 'anmelden'),
        PayloadHandler(subscribe, ['subscribe']),

        ApiAiHandler(unsubscribe, 'abmelden'),
        PayloadHandler(unsubscribe, ['unsubscribe']),

        ApiAiHandler(push, 'push'),
        PayloadHandler(push_step, ['push', 'next_state']),

        ApiAiHandler(wiki, 'wiki'),

        TextHandler(apiai_fulfillment, '.*'),
    ]

    def event_handler(data):
        """handle all incoming messages"""
        messaging_events = data['entry'][0]['messaging']
        logger.debug(messaging_events)

        for event in messaging_events:
            message = event.get('message')

            if message:
                text = message.get('text')

                if (text is not None
                    and event.get('postback') is None
                    and message.get('quick_reply') is None):

                    request = ai.text_request()
                    request.lang = 'de'
                    request.query = text
                    request.session_id = event['sender']['id']
                    response = request.getresponse()
                    nlp = json.loads(response.read().decode())
                    logging.info(nlp)
                    message['nlp'] = nlp

            for handler in handlers:
                try:
                    if handler.check_event(event):
                        try:
                            handler.handle_event(event)

                        except Exception as e:
                            logging.exception("Handling event failed")

                            try:
                                sender_id = event['sender']['id']
                                send_text(
                                    sender_id,
                                    'Huppsala, das hat nicht funktioniert :('
                                )

                                if int(sender_id) in ADMINS:
                                    txt = str(e)
                                    txt = txt.replace(PAGE_TOKEN, '[redacted]')
                                    txt = txt.replace(API_AI_TOKEN, '[redacted]')
                                    send_text(sender_id, txt)
                            except:
                                pass

                        finally:
                            break

                except:
                    logging.exception("Testing handler failed")

    return event_handler

handle_events = make_event_handler()


def push_notification():
    data = get_pushes()

    if not data:
        return

    user_list = FacebookUser.objects.values_list('uid', flat=True)

    unavailable_user_ids = list()

    for user in user_list:

        logger.debug("Send Push to: " + user)
        try:
            schema(data, user)
        except Exception as e:
            logger.exception("Push failed")
            try:
                if e.args[0]['code'] == 551:  # User is unavailable (probs deleted chat or account)
                    unavailable_user_ids.append(user)
                    logging.info('Removing user %s', user)
            except:
                pass

        sleep(2)

    for user in unavailable_user_ids:
        try:
            FacebookUser.objects.get(uid=user).delete()
        except:
            logging.exception('Removing user %s failed', user)


def push_breaking():
    data = get_breaking()

    if data is None or data.delivered:
        return

    user_list = FacebookUser.objects.values_list('uid', flat=True)

    for user in user_list:
        logger.debug("Send Push to: " + user)
        # media = '327430241009143'
        # send_attachment_by_id(user, media, 'image')
        try:
            send_push(user, data)
        except:
            logger.exception("Push failed")

        sleep(1)

    data.delivered = True
    data.save(update_fields=['delivered'])


schedule.every(30).seconds.do(push_breaking)
schedule.every().day.at("18:00").do(push_notification)
#schedule.every().day.at("08:00").do(push_notification)


def schedule_loop():
    while True:
        schedule.run_pending()
        sleep(1)

schedule_loop_thread = Thread(target=schedule_loop, daemon=True)
schedule_loop_thread.start()
