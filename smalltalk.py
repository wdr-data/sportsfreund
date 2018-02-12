import csv
from collections import defaultdict

from lib.dialogflow_api import api_call, simple_intent, parse_intent, POST, PUT


def load_all_existing_intents():
    resp = api_call('intents')

    return {
        i['name']: i['id']
        for i in resp
    }


def load_existing_intent(id):
    return api_call('intents', id=id)


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


def main():
    intent_ids = load_all_existing_intents()
    new_intents = load_csv()

    for name, data in new_intents.items():
        questions = data['questions']
        answers = data['answers']

        if name in intent_ids:
            intent = load_existing_intent(intent_ids[name])
            orig_name, orig_questions, orig_answers = parse_intent(intent)
            all_questions = list(set(questions) | set(orig_questions))
            all_answers = list(set(answers) | set(orig_answers))

            api_call(
                'intents',
                id=intent_ids[name],
                data=simple_intent(name, all_questions, all_answers),
                method=PUT
            )

        else:
            api_call(
                'intents',
                data=simple_intent(name, questions, answers),
                method=POST
            )


if __name__ == '__main__':
    main()
