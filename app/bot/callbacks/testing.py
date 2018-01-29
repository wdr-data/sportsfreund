
from backend.models import Push, Report

from lib.response import list_element, button_postback
from ..handlers.texthandler import TextHandler

"""
Contains callbacks and handlers for testing functionality or previewing content in the bot.
"""

def push(event, **kwargs):
    pushes = Push.last(count=4, only_published=False, delivered=True, by_date=False)
    if pushes.count() == 1:
        [event.send_buttons(
            'Es gibt derzeit nur einen Push.',
            buttons=[button_postback('Los geht`s',
                                    {'push': p.id, 'report': None, 'next_state': 'intro'})]
            )
        for p in pushes]
    elif pushes.count() == 0:
        event.send_text('Es gibt derzeit keinen Push.')

    event.send_list([
        list_element(
            str(p),
            subtitle=p.text[:80],
            buttons=[button_postback('Test',
                                     {'push': p.id, 'report': None, 'next_state': 'intro'})])
        for p in pushes
    ])


def report(event, **kwargs):
    reports = Report.last(count=4, only_published=False, delivered=True, by_date=False)

    event.send_list([
        list_element(
            str(r),
            subtitle=r.text[:80],
            buttons=[button_postback('Test',
                                     {'report': r.id, 'next_state': 'intro'})])
        for r in reports
    ])


handlers = [
    TextHandler(push, '#push'),
    TextHandler(report, '#meldung'),
]