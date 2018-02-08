from django.db import migrations

from lib import queue


def get_person(*args, **kwargs):
    #queue.queue_job("person.load_persons", {})
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0002_delete_attachment'),
    ]

    operations = [
        migrations.RunPython(get_person)
    ]

