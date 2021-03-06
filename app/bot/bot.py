import json
import logging
import os
from time import time

from apiai import ApiAI
from raven.contrib.django.raven_compat.models import client as error_client

from lib.config import FB_PAGE_TOKEN
from lib.response import Replyable
from lib.redis import redis_connection, HANDLED_UPDATES_FB
from metrics.models.activity import UserActivity
from metrics.models.unique_users import UserListing
# dirty
from .callbacks import dirty
from .callbacks import result, calendar, news, \
    subscription, video, medal, athlete, standing, sport
from .callbacks import testing
from .callbacks.default import (
    get_started, greetings, push, push_step, subscribe, unsubscribe, share_bot,
    apiai_fulfillment, wiki, countdown, korea_standard_time, story, story_payload, report,
    report_step, how_to, privacy, about_bot, company_details, btn_send_report)
from .handlers.apiaihandler import ApiAiHandler
from .handlers.payloadhandler import PayloadHandler
from .handlers.texthandler import TextHandler

logger = logging.getLogger(__name__)

DIALOGFLOW_TOKEN = os.environ.get('DIALOGFLOW_TOKEN', 'na')

ADMINS = [
1947930888581193, #Lisa
]


def make_event_handler():
    ai = ApiAI(DIALOGFLOW_TOKEN)

    handlers = []

    # testing
    handlers.extend(testing.handlers)
    handlers.extend(subscription.handlers)
    handlers.extend(result.handlers)
    handlers.extend(video.handlers)
    handlers.extend(medal.handlers)
    handlers.extend(athlete.handlers)
    handlers.extend(standing.handlers)
    handlers.extend(calendar.handlers)
    handlers.extend(news.handlers)

    handlers.extend([
        ApiAiHandler(greetings, 'gruss'),
        PayloadHandler(greetings, ['gruss']),

        PayloadHandler(get_started, ['start']),

        ApiAiHandler(subscribe, 'anmelden'),
        PayloadHandler(subscribe, ['subscribe']),

        ApiAiHandler(unsubscribe, 'abmelden'),
        PayloadHandler(unsubscribe, ['unsubscribe']),

        # menu handler
        PayloadHandler(privacy, ['privacy']),
        PayloadHandler(company_details, ['company_details']),
        PayloadHandler(about_bot, ['about']),
        PayloadHandler(how_to, ['how_to']),
        PayloadHandler(share_bot, ['share_bot']),
        ApiAiHandler(share_bot, 'share_bot'),

        ApiAiHandler(push, 'push.highlight'),
        PayloadHandler(push_step, ['push', 'report', 'next_state']),

        ApiAiHandler(report, 'push.report'),
        PayloadHandler(btn_send_report, ['report_sport', 'report_discipline']),
        PayloadHandler(report_step, ['report', 'next_state']),

        ApiAiHandler(korea_standard_time, 'korea_standard_time'),
        ApiAiHandler(countdown, 'countdown'),
        ApiAiHandler(countdown, 'info.olympia.countown_days'),
        ApiAiHandler(wiki, 'wiki'),

        #story
        PayloadHandler(story_payload, ['story', 'fragment']),

        # info.general
        ApiAiHandler(sport.api_sport,'info.general.sport', follow_up=True),
        # ApiAiHandler(sport.api_discipline,'info.general.discipline'),
        # ApiAiHandler(calendar.api_next, 'info.general.sport'),
        ApiAiHandler(calendar.api_next, 'info.general.discipline'),

        # info.match.result
        ApiAiHandler(result.api_winner ,'info.match.result.winner', follow_up=True),
        ApiAiHandler(result.api_podium, 'info.match.result.podium', follow_up=True),

        # info.match.calendar
        ApiAiHandler(calendar.api_next, 'info.match.calendar.next', follow_up=True),
        PayloadHandler(calendar.pl_entry_by_matchmeta, ['calendar.entry_by_matchmeta']),

        # info.medal
        ApiAiHandler(medal.medals, 'info.medals.filtered'),
        ApiAiHandler(medal.medals_table, 'info.medals.table'),

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

            if nlp['result']['contexts']:
                temp = nlp['result']['parameters']
                temp= {
                    i[:-2]: temp[i]
                    for i in temp
                    if i[:-2] in temp and not temp[i[:-2]]
                }
                nlp['result']['parameters'].update(temp)

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

    def event_handler(events, type):
        """handle all incoming messages"""
        for event in events:
            logging.debug('Incoming message : ' + str(event))
            message = event.get('message')
            sender_id = event['sender']['id']

            if message:
                msg_id = message['mid']
            else:
                msg_id = f'{sender_id}.{event["timestamp"]}'

            with redis_connection() as redis:
                already_handled = (redis.zadd(HANDLED_UPDATES_FB, time(), msg_id) == 0)

            if already_handled:
                logger.warning('Skipping duplicate event: %s', event)
                continue

            event = Replyable(event, type)

            UserListing.capture(sender_id)

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
                            error_client.captureException()
                            logging.exception("Handling event failed")

                            try:
                                event.send_text('Huppsala, das hat nicht funktioniert :(')

                                if int(sender_id) in ADMINS:
                                    txt = str(e)
                                    txt = txt.replace(FB_PAGE_TOKEN, '[redacted]')
                                    txt = txt.replace(DIALOGFLOW_TOKEN, '[redacted]')
                                    event.send_text(txt)
                            except:
                                pass

                        finally:
                            break

                except:
                    logging.exception("Testing handler failed")

    return event_handler


handle_events = make_event_handler()
