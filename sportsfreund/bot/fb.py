import os
import json
import logging
from time import sleep

import requests

from .models import Attachment

PAGE_TOKEN = os.environ.get('SPORTSFREUND_PAGE_TOKEN', 'na')
HUB_VERIFY_TOKEN = os.environ.get('SPORTSFREUND_HUB_VERIFY_TOKEN', 'na')

logger = logging.getLogger(__name__)


def send_text(recipient_id, text, quick_replies=None):
    """
    Sends a text message to a recipient, optionally with quick replies
    :param recipient_id: The user ID of the recipient
    :param text: The text to be sent
    :param quick_replies: A list of quick replies (optional)
    """

    prefix = ''
    max_len = 640

    while len(text) > max_len:
        max_len = 630

        split_at = text.rfind(' ', 0, max_len)
        part = text[:split_at or 630]

        send_text(recipient_id, prefix + part + '...')

        prefix = '...'
        text = text[split_at or 630:]

    message = {'text': prefix + text}

    # Facebook does not allow empty lists of quick replies
    if quick_replies:
        message['quick_replies'] = quick_replies

    payload = {
        'recipient': {
            'id': recipient_id,
        },
        'message': message,
    }

    send(payload)


def send_buttons(recipient_id, text, buttons):
    """
    Sends a text message with up to 3 buttons to a recipient
    :param recipient_id: The user ID of the recipient
    :param text: The text to be sent (max. 640 characters)
    :param buttons: Up to 3 buttons
    """

    prefix = ''
    max_len = 640

    while len(text) > max_len:
        max_len = 630

        split_at = text.rfind(' ', 0, max_len)
        part = text[:split_at or 630]

        send_text(recipient_id, prefix + part + '...')

        prefix = '...'
        text = text[split_at or 630:]

    payload = {
        'recipient': {
            'id': recipient_id
        },
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'button',
                    'text': prefix + text,
                    'buttons': buttons
                }
            }
        }
    }

    send(payload)

def send_generic(recipient_id, elements):
    """
    Sends a generic template with up to 10 elements to a recipient
    :param recipient_id: The user ID of the recipient
    :param elements: Up to 10 elements
    """

    payload = {
        'recipient': {
            'id': recipient_id
        },
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': elements
                }
            }
        }
    }

    send(payload)

def send_list(recipient_id, elements, top_element_style='compact', button=None):
    """
    Sends a list template to the recipient
    :param recipient_id: The user ID of the recipient
    :param elements: A list of 2-4 elements generated by list_element
    :param top_element_style: Can be either 'large' or 'compact'
    :param button: Optional button_postback to show at the end of the list
    :return:
    """
    payload = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "list",
                    "top_element_style": top_element_style,
                    "elements": elements,
                    "buttons": [
                        button
                    ]
                }
            }
        }
    }

    if not button:
        payload['message']['attachment']['payload'].pop('buttons')

    send(payload)


def list_element(title, subtitle=None, image_url=None, buttons=None, default_action=None):
    """
    Creates a dict to use with send_list
    :param title: Element title
    :param subtitle: Element subtitle (optional)
    :param image_url: Element image URL (optional)
    :param buttons: List of button_postback to show under the element (optional)
    :param default_action: Action generated by button_url (optional)
    :return: dict
    """
    payload = {
        "title": title,
        "image_url": image_url,
        "subtitle": subtitle,
        "default_action": default_action,
        "buttons": buttons
    }

    if not subtitle:
        payload.pop('subtitle')

    if not image_url:
        payload.pop('image_url')

    if not buttons:
        payload.pop('buttons')

    if not default_action:
        payload.pop('default_action')

    return payload


def button_postback(title, payload):
    """
    Creates a dict to use with send_buttons
    :param title: Button title
    :param payload: Button payload
    :return: dict
    """
    if isinstance(payload, (dict, list)):
        payload = json.dumps(payload)

    return {
        'type': 'postback',
        'title': title,
        'payload': payload,
    }

def button_web_url(title, url):
    """
    Creates a dict to send a web_url, can be used with generic_elements or send_buttons
    :param title: Content to show the receiver
    :return: dict
    """
    return {
        'type': 'web_url',
        'url': url,
        'title': title
    }

def button_share(generic_element):
    """
    Creates a dict to send a web_url, can be used with generic_elements or send_buttons
    :param title: Content to show the receiver
    :return: dict
    """
    button = {
        'type': 'element_share',
        'share_contents': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': generic_element
                }
            }
        }
    }

    if not generic_element:
        button.pop('share_contents')

    return button

def generic_element(title, subtitle=None, image_url=None, buttons=None):
    """
    Creates a dict to use with send_generic
    :param title: Content for receiver title
    :param subtitle: Content for receiver subtitle (optional)
    :param image_url: Content for receiver image to show by url (optional)
    :param button: Content for receiver button shown (optional)
    :return: dict
    """
    element = {
        "title": title,
        "subtitle": subtitle,
        "image_url": image_url,
        "buttons": buttons
    }

    if not subtitle:
        element.pop('subtitle')

    if not image_url:
        element.pop('image_url')

    if not buttons:
        element.pop('buttons')

    return element

def button_url(title, url, webview_height_ratio='full'):
    """
    Creates a dict to use with send_buttons
    :param title: Button title
    :param url: Button URL
    :param webview_height_ratio: Height of the Webview. Valid values: compact, tall, full.
    :return: dict
    """
    return {
        'type': 'web_url',
        'title': title,
        'url': url,
        'webview_height_ratio': webview_height_ratio
    }


def quick_reply(title, payload, image_url=None):
    """
    Creates a dict to use with send_text
    :param title: The title of the quick reply
    :param payload: The payload
    :param image_url: The image url (optional)
    :return: dict
    """
    if isinstance(payload, (dict, list)):
        payload = json.dumps(payload)

    payload_ = {
        'content_type': 'text',
        'title': title,
        'payload': payload,
      }

    if image_url:
        payload_['image_url'] = image_url

    return payload_


def send_attachment(recipient_id, url, type=None):
    """
    Send an attachment by URL. If the URL has not been uploaded before, it will be uploaded and the
    attachment ID will be saved to the database. If the URL has been uploaded before, the ID is
    fetched from the database. Then, the attachment is sent by ID.
    :param recipient_id: The user ID of the recipient
    :param url: The URL of the attachment
    :param type: Type of the attachment. If not defined, guess_attachment_type is used
    """
    try:
        attachment = Attachment.objects.get(url=url)
        attachment_id = attachment.attachment_id
    except Attachment.DoesNotExist:
        attachment_id = upload_attachment(url, type)
        if attachment_id is None:
            raise ValueError('Uploading attachment with URL %s failed' % url)
        Attachment(url=url, attachment_id=attachment_id).save()

    send_attachment_by_id(recipient_id, attachment_id, type or guess_attachment_type(url))


def send_attachment_by_id(recipient_id, attachment_id, type):
    """
    Sends an attachment via ID
    :param recipient_id: The user ID of the recipient
    :param attachment_id: The attachment ID returned by upload_attachment
    :param type: The attachment type (see guess_attachment_type)
    """

    recipient = {'id': recipient_id}

    # create a media object
    media = {'attachment_id': attachment_id}

    # add the image object to an attachment of type "image"
    attachment = {
        'type': type,
        'payload': media
    }

    # add the attachment to a message instead of "text"
    message = {'attachment': attachment}

    # now create the final payload with the recipient
    payload = {
        'recipient': recipient,
        'message': message
    }
    send(payload)


def send(payload):
    """Sends a payload via the graph API"""
    logger.debug("JSON Payload: " + json.dumps(payload))
    headers = {'Content-Type': 'application/json'}
    r = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + PAGE_TOKEN,
                      data=json.dumps(payload),
                      headers=headers)
    response = r.content.decode()
    logger.debug(response)
    error = json.loads(response).get('error')
    if error:
        raise Exception(error)


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
                "https://graph.facebook.com/v2.6/me/message_attachments?access_token=" + PAGE_TOKEN,
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
