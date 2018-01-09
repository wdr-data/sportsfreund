import json
import logging

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from lib.config import FB_HUB_VERIFY_TOKEN
from lib.response import SenderTypes
from . import bot

logger = logging.getLogger(__name__)


@csrf_exempt
def webhook_fb(request):
    if request.method == 'GET':
        if request.GET.get('hub.verify_token') == FB_HUB_VERIFY_TOKEN:
            return HttpResponse(request.GET['hub.challenge'], content_type="text/plain")
        else:
            return HttpResponse('Hello World!', content_type="text/plain")

    elif request.method == 'POST':
        data = json.loads(request.body.decode())
        events = data['entry'][0]['messaging']
        try:
            logger.debug('handling events')
            bot.handle_events(events, type=SenderTypes.FACEBOOK)

        except:
            logger.exception("Error handling messages")
        return HttpResponse("ok", content_type="text/plain")

