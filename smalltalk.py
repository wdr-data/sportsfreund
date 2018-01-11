import os
import json
import csv
from collections import defaultdict

import requests

TOKEN = os.environ['DIALOGFLOW_DEV_TOKEN']

GET, POST, PUT = range(3)


def api_call(endpoint, id='', params=None, data=None, method=GET):

    if not params:
        params = {}

    params['v'] = '20150910'
    params['lang'] = 'de'

    params_url = '&'.join(f'{k}={v}' for k, v in params.items())
    url = f'https://api.dialogflow.com/v1/{endpoint}/{id}?{params_url}'

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

    r = the_method(url, headers=headers, data=data)

    if r.status_code == 200:
        return r.json()

    else:
        raise ValueError(f'Loading URL {url} failed with code {r.status_code}')


def load_all_existing_intents():
    resp = api_call('intents')

    return {
        i['name']: i['id']
        for i in resp
    }


def load_existing_intent(id):
    resp = api_call('intents', id)

    return resp


def load_csv():
    filename = 'Dialogflow_intents - Smalltalk_sportsfreund.csv'

    intents = defaultdict(lambda: defaultdict(list))

    with open(filename, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip first line

        for row in reader:
            intent = row[1]
            question = row[2]
            answer = row[3]

            if question:
                intents[intent]['questions'].append(question)

            if answer:
                intents[intent]['answers'].append(answer)

    return intents


def make_response(intent_name, questions, answers):
    resp = {
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

    return resp


def parse_intent(data):
    name = data['name']
    questions = [obj['data'][0]['text'] for obj in data['userSays']]
    answers = data['responses'][0]['messages'][0]['speech']
    return name, questions, answers


def main():
    intent_ids = load_all_existing_intents()
    new_intents = load_csv()

    for name, data in new_intents.items():
        questions = data['questions']
        answers = data['answers']

        if name in intent_ids:
            intent = load_existing_intent(intent_ids[name])
            print('Existing:', intent['name'])
            orig_name, orig_questions, orig_answers = parse_intent(intent)
            all_questions = list(set(questions) | set(orig_questions))
            all_answers = list(set(answers) | set(orig_answers))

            api_call(
                'intents',
                id=intent_ids[name],
                data=json.dumps(make_response(name, all_questions, all_answers)),
                method=PUT
            )

        else:
            print('New:     ', name)
            print(name, questions, answers)
            api_call(
                'intents',
                data=json.dumps(make_response(name, questions, answers)),
                method=POST
            )


if __name__ == '__main__':
    main()
