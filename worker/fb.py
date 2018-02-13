import os
import json
import logging

import gevent
import requests

from feeds.models.subscription import Subscription
from lib.attachment import Attachment
from lib.facebook import upload_attachment, guess_attachment_type
from lib.response import Replyable, SenderTypes
from lib.sent_tracking import UserSentTracking
from worker import BaseTask

logger = logging.getLogger(__name__)

PAGE_TOKEN = os.environ.get('FB_PAGE_TOKEN', 'na')


class FacebookError(Exception):
    def __init__(self, error):
        super()
        self.message = error.get('message')
        self.type = error.get('type')
        self.code = error.get('code')
        self.subcode = error.get('error_subcode')
        self.fbtrace = error.get('fbtrace_id')

    def __str__(self):
        return self.message


class Send(BaseTask):

    def run(self, params):
        """Sends a payload via the graph API"""
        payload = params['payload']
        id = params['sending_id']
        for i in range(10):
            tracking = UserSentTracking.by_id(payload['recipient']['id'])
            if not ('last_sent' in tracking):
                break
            if tracking.last_sent + 1 == id:
                break
            gevent.sleep(0.5)

        logger.debug("JSON Payload: " + json.dumps(payload))

        headers = {'Content-Type': 'application/json'}
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params={'access_token': PAGE_TOKEN},
                          data=json.dumps(payload),
                          headers=headers)
        response = r.content.decode()

        logger.debug(response)

        error = json.loads(response).get('error')
        if error:
            if int(error.get('code', 0)) == 551:  # Unavailable
                Subscription.collection.delete_many({'psid': payload['recipient']['id']})
            else:
                raise FacebookError(error)
        else:
            UserSentTracking.set_sent(payload['recipient']['id'], id)


class SendAttachment(BaseTask):

    def run(self, params):
        """Sends a payload via the graph API"""

        recipient_id = params['recipient_id']
        event = Replyable({'sender': {'id': recipient_id}}, SenderTypes.FACEBOOK)

        url = params['url']
        type = params['type']

        try:
            attachment = Attachment.query(url=url)[0]
            attachment_id = attachment.attachment_id
        except IndexError:
            attachment_id = upload_attachment(url, type)
            if attachment_id is None:
                raise ValueError('Uploading attachment with URL %s failed' % url)
            Attachment.create(url=url, attachment_id=attachment_id)

        event.send_attachment_by_id(attachment_id, type or guess_attachment_type(url))
