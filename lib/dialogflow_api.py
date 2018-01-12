import os
import json

import requests

TOKEN = os.environ['DIALOGFLOW_DEV_TOKEN']
GET, POST, PUT = range(3)


def api_call(endpoint, *, id='', attribute=None, params=None, data=None, method=GET):
    """
    Makes a call to the Dialogflow API
    :param endpoint: API endpoint (eg. 'intents')
    :param id: The UUID of an API object
    :param attribute: The attribute you want to access ('entries' in '/entities/{id}/entries')
    :param params: Additional parameters you want to pass. By default, 'v' and 'lang' are passed.
    :param data: JSON-serializable data to be sent
    :param method: Can be GET (querying objects), POST (adding objects) or PUT (update objects)
    :return:
    """

    if not params:
        params = {}

    params['v'] = '20150910'
    params['lang'] = 'de'

    params_url = '&'.join(f'{k}={v}' for k, v in params.items())
    url = f'https://api.dialogflow.com/v1/{endpoint}'

    if id:
        url += f'/{id}'

    if attribute:
        url += f'/{attribute}'

    url += f'?{params_url}'

    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
    }

    methods = {
        GET: requests.get,
        POST: requests.post,
        PUT: requests.put,
    }

    the_method = methods[method]

    r = the_method(url, headers=headers, data=json.dumps(data))

    if r.status_code == 200:
        return r.json()

    else:
        raise ValueError(f'Loading URL {url} failed with code {r.status_code}')


def simple_intent(intent_name, questions, answers):
    return {
        'name': intent_name,
        'contexts': [],
        'events': [],
        'fallbackIntent': False,
        'followUpIntents': [],
        'priority': 500000,
        'responses': [{
            'messages': [{'speech': answers, 'type': 0}],
            'parameters': [],
            'resetContexts': False,
            'action': intent_name,
            'affectedContexts': [],
            'defaultResponsePlatforms': {},
        }],
        'templates': [],
        'userSays': [
            {
                'count': 0,
                'data': [{'text': question}],
            } for question in questions
        ],
        'webhookForSlotFilling': False,
        'webhookUsed': False,
    }


def parse_intent(data):
    name = data['name']
    questions = [obj['data'][0]['text'] for obj in data['userSays']]
    answers = data['responses'][0]['messages'][0]['speech']
    return name, questions, answers
