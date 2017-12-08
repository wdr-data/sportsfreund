import os
import json
import logging
import requests
from mrq.task import Task

from lib.attachment import Attachment
from lib.facebook import upload_attachment, guess_attachment_type
from lib.response import send_attachment_by_id

logger = logging.getLogger(__name__)

PAGE_TOKEN = os.environ.get('FB_PAGE_TOKEN', 'na')


class Send(Task):

    def run(self, params):
        """Sends a payload via the graph API"""
        payload = params['payload']
        logger.debug("JSON Payload: " + json.dumps(payload))

        headers = {'Content-Type': 'application/json'}
        r = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + PAGE_TOKEN,
                          data=json.dumps(payload),
                          headers=headers)
        response = r.content.decode()

        logger.debug(response)

        error = json.loads(response).get('error')
        if error:
            raise Exception(error)


class SendAttachment(Task):

    def run(self, params):
        """Sends a payload via the graph API"""

        recipient_id = params['recipient_id']
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

        send_attachment_by_id(recipient_id, attachment_id, type or guess_attachment_type(url))
