from datetime import date, time, datetime

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib import messages

from bot.fb import upload_attachment, UploadFailedError


def default_pub_date():
    now = timezone.now()
    default = datetime(now.year, now.month, now.day, hour=18, minute=00)
    return default


class Push(models.Model):

    class Meta:
        verbose_name = 'Push'
        verbose_name_plural = 'Pushes'

    headline = models.CharField('Titel', max_length=200, null=False)
    text = models.CharField('Intro-Text', max_length=200, null=False)

    pub_date = models.DateTimeField(
        'Versenden am',
        default=default_pub_date)

    published = models.BooleanField('Freigegeben', null=False, default=False)


class Report(models.Model):

    class Meta:
        verbose_name = 'Meldung'
        verbose_name_plural = 'Meldungen'

    headline = models.CharField('Überschrift', max_length=200, null=False)
    text = models.CharField('Intro-Text', max_length=200, null=False)
    media = models.FileField('Medien-Anhang Intro', null=True, blank=True)
    media_note = models.CharField(
        'Anmerkung', max_length=128, null=True, blank=True, help_text='z. B. Bildrechte')
    attachment_id = models.CharField(
        'Facebook Attachment ID', max_length=64, null=True, blank=True,
        help_text="Wird automatisch ausgefüllt")

    push = models.ForeignKey('Push', on_delete=models.SET_NULL,
                             related_name='reports', related_query_name='report', null=True)

    created = models.DateTimeField(
        'Erstellt',
        default=timezone.now)

    published = models.BooleanField('Freigegeben', null=False, default=False)

    delivered = models.BooleanField(
        'Versendet', null=False, default=False,
        help_text="Wurde diese Meldung bereits in einem Highlights-Push vom Bot versendet?")

    def __str__(self):
        return '%s - %s' % (self.created.strftime('%d.%m.%Y'), self.headline)

    def _save(self, *args, **kwargs):
        try:
            request = kwargs.pop('request')
        except KeyError:
            request = None

        try:
            orig = Report.objects.get(id=self.id)
        except Report.DoesNotExist:
            orig = None

        orig_media = str(orig.media) if orig else ''

        updated = (
            not orig and str(self.media)
            or str(self.media) != orig_media
        )

        super().save(*args, **kwargs)

        if updated:
            if str(self.media):
                url = settings.SITE_URL + settings.MEDIA_URL + str(self.media)
                try:
                    attachment_id = upload_attachment(url)
                    self.attachment_id = attachment_id
                except UploadFailedError:
                    if request:
                        messages.warning(
                            request,
                            "Upload von Facebook Attachment fehlgeschlagen: %s" % self.media)
                    else:
                        raise

            else:
                self.attachment_id = None

            self.save()

    def update_attachment(self):
        if str(self.media):
            url = settings.SITE_URL + settings.MEDIA_URL + str(self.media)
            attachment_id = upload_attachment(url)
            self.attachment_id = attachment_id
        else:
            self.attachment_id = None


class ReportFragment(models.Model):

    class Meta:
        verbose_name = 'Meldungs-Fragment'
        verbose_name_plural = 'Meldungs-Fragmente'

    report = models.ForeignKey('Report', on_delete=models.CASCADE, related_name='fragments',
                               related_query_name='fragment')

    question = models.CharField('Frage', max_length=20, null=False, blank=False)
    text = models.CharField('Text', max_length=600, null=False, blank=False)
    media = models.FileField('Medien-Anhang', null=True, blank=True)
    media_note = models.CharField(
        'Anmerkung', max_length=128, null=True, blank=True, help_text='z. B. Bildrechte')
    attachment_id = models.CharField(
        'Facebook Attachment ID', max_length=64, null=True, blank=True,
        help_text="Wird automatisch ausgefüllt")

    def __str__(self):
        return '%s - %s' % (self.report.headline, self.question)

    def _save(self, *args, **kwargs):
        try:
            request = kwargs.pop('request')
        except KeyError:
            request = None

        try:
            orig = ReportFragment.objects.get(id=self.id)
        except ReportFragment.DoesNotExist:
            orig = None

        orig_media = str(orig.media) if orig else ''

        updated = (
            not orig and str(self.media)
            or str(self.media) != orig_media
        )

        super().save(*args, **kwargs)

        if updated:
            if str(self.media):
                url = settings.SITE_URL + settings.MEDIA_URL + str(self.media)
                try:
                    attachment_id = upload_attachment(url)
                    self.attachment_id = attachment_id
                except UploadFailedError:
                    if request:
                        messages.warning(
                            request,
                            "Upload von Facebook Attachment fehlgeschlagen: %s" % self.media)
                    else:
                        raise

            else:
                self.attachment_id = None

            self.save()

    def update_attachment(self):
        if str(self.media):
            url = settings.SITE_URL + settings.MEDIA_URL + str(self.media)
            attachment_id = upload_attachment(url)
            self.attachment_id = attachment_id
        else:
            self.attachment_id = None


class FacebookUser(models.Model):

    class Meta:
        verbose_name = 'Facebook User'
        verbose_name_plural = 'Facebook User'

    uid = models.CharField('User ID', max_length=64, null=False, unique=True)
    state = models.CharField('State', max_length=64, null=True, blank=True)
    add_date = models.DateTimeField('Hinzugefügt am', default=timezone.now)

    def __str__(self):
        return str(self.uid)


class Wiki(models.Model):
    class Meta:
        verbose_name = 'Wiki-Eintrag'
        verbose_name_plural = 'Wiki-Einträge'

    input = models.CharField('Eingabe', max_length=128, null=False, unique=True,
                             help_text="Der Eingabetext des Nutzers")
    output = models.CharField('Antwort', max_length=640, null=True, blank=True,
                              help_text="Die Antwort, die der Bot auf die Eingabe geben soll")
    media = models.FileField('Medien-Anhang', null=True, blank=True)
    attachment_id = models.CharField(
        'Facebook Attachment ID', max_length=64, null=True, blank=True,
        help_text="Wird automatisch ausgefüllt")

    def save(self, *args, **kwargs):
        try:
            orig = Wiki.objects.get(id=self.id)
        except Wiki.DoesNotExist:
            orig = None

        field = self.media
        orig_field = orig.media if orig else ''

        if (orig and str(field) and str(field) == str(orig_field)
                or not str(field) and not str(orig_field)):
            super().save(*args, **kwargs)
            return

        super().save(*args, **kwargs)

        field = self.media
        if str(field):
            url = settings.SITE_URL + settings.MEDIA_URL + str(field)
            attachment_id = upload_attachment(url)
            self.attachment_id = attachment_id

        else:
            self.attachment_id = None

        self.save()

    def __str__(self):
        return self.input


class Info(models.Model):
    class Meta:
        verbose_name = 'Info'
        verbose_name_plural = 'Infos'

    title = models.CharField('Titel', max_length=128, null=False, unique=True,
                             help_text="Hinweis: Wird nicht ausgespielt")
    content = models.CharField('Inhalt', max_length=600, null=True, blank=True,
                              help_text="Text der Info")
    media = models.FileField('Medien-Anhang', null=True, blank=True)
    attachment_id = models.CharField(
        'Facebook Attachment ID', max_length=64, null=True, blank=True,
        help_text="Wird automatisch ausgefüllt")

    def save(self, *args, **kwargs):
        try:
            orig = Info.objects.get(id=self.id)
        except Info.DoesNotExist:
            orig = None

        field = self.media
        orig_field = orig.media if orig else ''

        if (orig and str(field) and str(field) == str(orig_field)
                or not str(field) and not str(orig_field)):
            super().save(*args, **kwargs)
            return

        super().save(*args, **kwargs)

        field = self.media
        if str(field):
            url = settings.SITE_URL + settings.MEDIA_URL + str(field)
            attachment_id = upload_attachment(url)
            self.attachment_id = attachment_id

        else:
            self.attachment_id = None

        self.save()

    def __str__(self):
        return self.title
