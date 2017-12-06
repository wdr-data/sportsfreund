
import datetime

from lib.response import send_text


def api_countdown_days(event, **kwargs):
    sender_id = event['sender']['id']
    today = datetime.datetime.today()
    olympia_start = datetime.datetime(2018, 2, 9, 12)
    delta = olympia_start - today

    reply = 'Bis zu den Olympischen Winterspiele sind es noch {days} Tage, {hours} Stunden und {minutes} Minuten.'.format(
            days=delta.days,
            hours=delta.seconds//3600,
            minutes=(delta.seconds%3600)//60
        )
    send_text(sender_id, reply)
