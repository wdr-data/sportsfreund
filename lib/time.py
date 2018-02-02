import requests
from datetime import timedelta, datetime

from .config import FB_PAGE_TOKEN
from .mongodb import db

collection = db.user_timezone_cache


def localtime_format(date, event, is_olympia=False, format="%H:%M Uhr"):
    offset = 1

    user_id = event['sender']['id']
    try:
        cache = collection.find_one({'psid': user_id})
    except:
        cache = None
    if cache and cache['expires_at'] > datetime.now():
        offset = cache['offset']
    else:
        res = requests.get(f"https://graph.facebook.com/v2.6/{user_id}",
                           params={
                               'access_token': FB_PAGE_TOKEN,
                               'fields': 'timezone',
                           })
        if res.status_code == requests.codes.ok:
            offset = res.json().get('timezone')
            collection.replace_one({'psid': user_id}, {
                'psid': user_id,
                'offset': offset,
                'expires_at': datetime.now() + timedelta(days=1)
            }, upsert=True)

    user_time = date + timedelta(hours=offset)
    timestring = f"{user_time.strftime(format)} (bei dir)"

    if is_olympia:
        korean_time = date + timedelta(hours=9)
        timestring += f" - {korean_time.strftime(format)} (in Korea)"

    return timestring
