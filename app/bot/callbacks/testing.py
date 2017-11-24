
from backend.models import Push, Report
from ..handlers.texthandler import TextHandler
from ..fb import send_list, list_element, button_postback
from .shared import schema

"""
Contains callbacks and handlers for testing functionality or previewing content in the bot.
"""

def push(event, **kwargs):
    sender_id = event['sender']['id']

    pushes = Push.last(count=4, only_published=False, delivered=True, by_date=False)

    send_list(
        sender_id,
        [
            list_element(
                str(p),
                subtitle=p.text[:80],
                buttons=[button_postback('Test',
                                         {'push': p.id, 'report': None, 'next_state': 'intro'})])
            for p in pushes
        ]
    )


def report(event, **kwargs):
    sender_id = event['sender']['id']

    reports = Report.last(count=4, only_published=False, delivered=True, by_date=False)

    send_list(
        sender_id,
        [
            list_element(
                str(r),
                subtitle=r.text[:80],
                buttons=[button_postback('Test',
                                         {'report': r.id, 'next_state': 'intro'})])
            for r in reports
        ]
    )


handlers = [
    TextHandler(push, '#push'),
    TextHandler(report, '#meldung'),
]