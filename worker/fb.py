import os
import json
import logging
import requests
from mrq.task import Task

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
