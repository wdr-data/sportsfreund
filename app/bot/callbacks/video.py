import random

from ..handlers.apiaihandler import ApiAiHandler
from feeds.models.video import Video
from lib.response import send_attachment, send_text

NO_VIDEO_FOUND = [
    'Boah sorry, dazu finde ich gerade gar nix 😅',
    'Hmm da ist nix zu machen, ich finde kein einziges Video dazu 😔'
]


def api_asking(event, parameters, **kwargs):
    sender_id = event['sender']['id']

    keywords = list(param for param in parameters.values() if param)
    vid = Video.by_keyword(keywords, max_duration=120)

    send_text(sender_id, 'Ich schaue mal in meinen Archiven... 🔍')

    if vid:
        send_text(sender_id, vid.summary)
        send_attachment(sender_id, vid.video_url)

    else:
        vid = Video.by_keyword(keywords, max_duration=100000)
        if vid:
            send_text(sender_id, f"{vid.summary}\n\nDieses Video ist leider zu lang für Facebook, "
                                 f"aber du kannst es unter diesem Link anschauen: {vid.url}")
        else:
            send_text(sender_id, random.choice(NO_VIDEO_FOUND))


handlers = [
    ApiAiHandler(api_asking, 'video.asking'),
]
