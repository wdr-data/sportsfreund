from django.db import models

# Create your models here.


class Attachment(models.Model):

    class Meta:
        verbose_name = 'Facebook Attachment'
        verbose_name_plural = 'Facebook Attachments'

    url = models.CharField('URL', max_length=1024, null=False, unique=True)
    attachment_id = models.CharField('Attachment ID', max_length=128, null=False, blank=False)

    def __str__(self):
        return str(self.url)
