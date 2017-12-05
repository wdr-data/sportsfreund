import os
import logging
import json
import requests
from time import sleep

from .config import FB_PAGE_TOKEN

logger = logging.getLogger(__name__)


class UploadFailedError(ValueError):
    pass


def upload_attachment(url, type=None, retries=3):
    """
    Uploads an attachment and returns the attachment ID

    :param url The URL of the file to upload
    :param type The type of the file. Can be 'image', 'video' or 'audio'.
        If not provided, it will be guessed from the file extension.
    :raises UploadFailedError if the upload failed after the specified number of retries
    """
    payload = {
        "message": {
            "attachment": {
                "type": type or guess_attachment_type(url),
                "payload": {
                    "url": url,
                    "is_reusable": True,
                }
            }
        }
    }
    logger.debug("JSON Payload: " + json.dumps(payload))
    headers = {'Content-Type': 'application/json'}

    for i in range(retries):
        try:
            r = requests.post(
                "https://graph.facebook.com/v2.6/me/message_attachments?access_token=" + FB_PAGE_TOKEN,
                data=json.dumps(payload),
                headers=headers)
            return json.loads(r.content.decode())['attachment_id']

        except:
            logging.exception("Uploading failed, retry %s/%s", i + 1, retries)
            sleep(1)

    else:
        raise UploadFailedError('Uploading file %s with type %s failed.', url, type)


def guess_attachment_type(filename):
    """Guesses the attachment type from the file extension"""
    ext = os.path.splitext(filename)[1].lower()
    types = {
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.mp4': 'video',
        '.mp3': 'audio',
    }

    return types.get(ext, None)
