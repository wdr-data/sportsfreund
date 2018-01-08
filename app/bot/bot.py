import json
import logging
import os

from apiai import ApiAI

from lib.config import FB_PAGE_TOKEN
from lib.response import send_text
# dirty
from .callbacks import dirty
from .callbacks import result, calendar, olympia, subscription, video
from .callbacks import testing
from .callbacks.default import (
    get_started, start_message, greetings, push, push_step, subscribe, unsubscribe, share_bot,
    apiai_fulfillment, wiki, countdown, korea_standard_time, story, story_payload, report,
    report_step)
from .handlers.apiaihandler import ApiAiHandler
from .handlers.payloadhandler import PayloadHandler
from .handlers.texthandler import TextHandler

logger = logging.getLogger(__name__)

DIALOGFLOW_TOKEN = os.environ.get('DIALOGFLOW_TOKEN', 'na')

ADMINS = [
]


def make_event_handler():
    ai = ApiAI(DIALOGFLOW_TOKEN)

    handlers = []

    # testing
    handlers.extend(testing.handlers)
    handlers.extend(subscription.handlers)
    handlers.extend(result.handlers)
    handlers.extend(video.handlers)

    handlers.extend([
        ApiAiHandler(greetings, 'gruss'),
        PayloadHandler(greetings, ['gruss']),

        PayloadHandler(get_started, ['start']),
        PayloadHandler(start_message, ['start_message']),

        ApiAiHandler(subscribe, 'anmelden'),
        PayloadHandler(subscribe, ['subscribe']),

        ApiAiHandler(unsubscribe, 'abmelden'),
        PayloadHandler(unsubscribe, ['unsubscribe']),

        PayloadHandler(share_bot, ['share_bot']),
        ApiAiHandler(share_bot, 'share_bot'),

        ApiAiHandler(push, 'push.highlight'),
        PayloadHandler(push_step, ['push', 'report', 'next_state']),

        ApiAiHandler(report, 'push.report'),
        PayloadHandler(report_step, ['report', 'next_state']),

        ApiAiHandler(korea_standard_time, 'korea_standard_time'),
        ApiAiHandler(countdown, 'countdown'),
        ApiAiHandler(wiki, 'wiki'),

        #story
        PayloadHandler(story_payload, ['story', 'fragment']),

        # info.general
        # ApiAiHandler(general.api_sport,'info.general.sport'),
        # ApiAiHandler(general.api_discipline,'info.general.discipline'),
        ApiAiHandler(calendar.api_next, 'info.general.sport'),
        ApiAiHandler(calendar.api_next, 'info.general.discipline'),

        # info.match.result
        ApiAiHandler(result.api_winner ,'info.match.result.winner', follow_up=True),
        ApiAiHandler(result.api_podium, 'info.match.result.podium', follow_up=True),

        # info.match.calendar
        ApiAiHandler(calendar.api_next, 'info.match.calendar.next', follow_up=True),
        PayloadHandler(calendar.pl_entry_by_matchmeta, ['calendar.entry_by_matchmeta']),

        # info.olympia
        ApiAiHandler(olympia.api_countdown_days, 'info.olympia.countown_days'),


        # dirty
        ApiAiHandler(dirty.force_start, 'dirty.force_start'),
        TextHandler(apiai_fulfillment, '.*')

    ])

    def query_api_ai(event):
        """
        Runs the message text through api.ai if the message is a regular text message and returns
        the response dict. Returns None if the message is not a regular text message (buttons etc).
        """
        message = event['message']
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

            nlp['result']['parameters'] = {
                k: v or None for k, v in nlp['result']['parameters'].items()}

            logging.debug(nlp)
            return nlp
        else:
            return None

    def api_ai_story_hook(event, nlp):
        """Checks if the api.ai intent is a story hook and runs it.

        :returns True if the intent was a story hook and it was proccessed successfully, else False
        """
        try:
            if nlp and nlp['result']['metadata']['intentName'].startswith('story:'):
                slug = nlp['result']['metadata']['intentName'][len('story:'):]
                story(event, slug, fragment_nr=None)
                return True
        except:
            logging.exception("Story failed")

        return False

    def event_handler(data):
        """handle all incoming messages"""
        messaging_events = data['entry'][0]['messaging']
        logger.debug(messaging_events)

        for event in messaging_events:
            message = event.get('message')

            if message:
                nlp = query_api_ai(event)

                if nlp:
                    message['nlp'] = nlp

                api_ai_story_hook(event, nlp)

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
                                    txt = txt.replace(FB_PAGE_TOKEN, '[redacted]')
                                    txt = txt.replace(DIALOGFLOW_TOKEN, '[redacted]')
                                    send_text(sender_id, txt)
                            except:
                                pass

                        finally:
                            break

                except:
                    logging.exception("Testing handler failed")

    return event_handler


handle_events = make_event_handler()
