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
from .callbacks.default import (
    get_started, start_message, greetings, push, push_step, subscribe, unsubscribe,
    apiai_fulfillment, wiki, countdown, korea_standard_time, story)
from .callbacks.shared import get_push, schema

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

        ApiAiHandler(korea_standard_time, 'korea_standard_time'),
        ApiAiHandler(countdown, 'countdown'),
        ApiAiHandler(wiki, 'wiki'),

        TextHandler(apiai_fulfillment, '.*'),
    ]

    def event_handler(data):
        """handle all incoming messages"""
        messaging_events = data['entry'][0]['messaging']
        logger.debug(messaging_events)

        for event in messaging_events:
            message = event.get('message')
            nlp = None

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

            try:
                if nlp and nlp['result']['metadata']['intentName'].startswith('story:'):
                    slug = nlp['result']['metadata']['intentName'][len('story:'):]
                    story(event, slug, fragment_nr=None)
            except:
                logging.exception("Story failed")

    return event_handler


def push_notification():
    push = get_push()

    if not push:
        return

    user_list = FacebookUser.objects.values_list('uid', flat=True)

    unavailable_user_ids = list()

    for user in user_list:

        logger.debug("Send Push to: " + user)
        try:
            schema(push, user)
        except Exception as e:
            logger.exception("Push failed")
            try:
                if e.args[0]['code'] == 551:  # User is unavailable (probs deleted chat or account)
                    unavailable_user_ids.append(user)
                    logging.info('Removing user %s', user)
            except:
                pass

        sleep(.5)

    for user in unavailable_user_ids:
        try:
            FacebookUser.objects.get(uid=user).delete()
        except:
            logging.exception('Removing user %s failed', user)

    push.delivered = True
    push.save()


def schedule_loop():
    while True:
        schedule.run_pending()
        sleep(1)


handle_events = make_event_handler()

schedule.every(30).seconds.do(push_notification)
schedule_loop_thread = Thread(target=schedule_loop, daemon=True)
schedule_loop_thread.start()
