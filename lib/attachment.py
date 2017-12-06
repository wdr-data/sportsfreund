from lib.model import Model
from lib.mongodb import db


class Attachment(Model):

    collection = db.attachments

    @classmethod
    def create(cls, url: str, attachment_id: str):

        cls.collection.replace_one(
            {'url': url, 'attachment_id': attachment_id},
            {'url': url, 'attachment_id': attachment_id},
            upsert=True)
