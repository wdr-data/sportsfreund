import random

from ..handlers.apiaihandler import ApiAiHandler
from feeds.models.video import Video

NO_VIDEO_FOUND = [
    'Boah sorry, dazu finde ich gerade gar nix 😅',
    'Hmm da ist nix zu machen, ich finde kein einziges Video dazu 😔'
]


def api_asking(event, parameters, **kwargs):
    keywords = list(param for param in parameters.values() if param)
    vid = Video.by_keyword(keywords, max_duration=120)

    event.send_text('Ich schaue mal in meinen Archiven... 🔍')

    if vid:
        event.send_text(vid.summary)
        event.send_attachment(vid.video_url)

    else:
        vid = Video.by_keyword(keywords, max_duration=100000)
        if vid:
            event.send_text(f"{vid.summary}\n\nDieses Video ist leider zu lang für Facebook, "
                            f"aber du kannst es unter diesem Link anschauen: {vid.url}")
        else:
            event.send_text(random.choice(NO_VIDEO_FOUND))


handlers = [
    ApiAiHandler(api_asking, 'video.asking'),
]
