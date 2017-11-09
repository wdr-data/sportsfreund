from threading import Thread
from time import sleep
import schedule
import logging

from backend.models import FacebookUser
from .callbacks.shared import get_push, schema

logger = logging.getLogger(__name__)


def push_notification():
    push = get_push()

    if not push:
        return

    user_list = FacebookUser.objects.values_list('uid', flat=True)

    unavailable_user_ids = list()

    for user in user_list:

        logger.debug("Send Push to: " + user)
        try:
            schema(push, user)
        except Exception as e:
            logger.exception("Push failed")
            try:
                if e.args[0]['code'] == 551:  # User is unavailable (probs deleted chat or account)
                    unavailable_user_ids.append(user)
                    logging.info('Removing user %s', user)
            except:
                pass

        sleep(.5)

    for user in unavailable_user_ids:
        try:
            FacebookUser.objects.get(uid=user).delete()
        except:
            logging.exception('Removing user %s failed', user)

    push.delivered = True
    push.save()


def schedule_loop():
    while True:
        schedule.run_pending()
        sleep(1)


def start_scheduler():
    schedule.every(30).seconds.do(push_notification)
    schedule_loop_thread = Thread(target=schedule_loop, daemon=True)
    schedule_loop_thread.start()
