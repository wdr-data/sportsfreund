from datetime import datetime

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from sortedm2m.fields import SortedManyToManyField

from lib import queue
from lib.facebook import upload_attachment
from feeds.config import supported_sports


def default_pub_date():
    now = timezone.now()
    default = datetime(now.year, now.month, now.day, hour=18, minute=00)
    return default


HIGHLIGHT_CHECK_INTERVAL = 60


class Push(models.Model):
    """
    Pushes fassen Meldungen zusammen. Diese Meldungen werden zum jeweils festgelegten Zeitpunkt
    an alle Abonnenten versandt.
    """

    class Meta:
        verbose_name = 'Push'
        verbose_name_plural = 'Pushes'

    headline = models.CharField('Titel', max_length=200, null=False)
    text = models.CharField('Intro-Text', max_length=640, null=False)

    outro = models.CharField('Outro-Text', max_length=640, blank=True, null=False)

    reports = SortedManyToManyField('Report', related_name='pushes', verbose_name='Meldungen')

    pub_date = models.DateTimeField(
        'Versenden am',
        default=default_pub_date)

    published = models.BooleanField(
        'Freigegeben', null=False, default=False,
        help_text='Solange dieser Haken nicht gesetzt ist, wird dieser Push nicht versendet, '
                  'auch wenn der konfigurierte Zeitpunkt erreicht wird.')

    delivered = models.BooleanField('Versendet', null=False, default=False)

    def __str__(self):
        return '%s - %s' % (self.pub_date.strftime('%d.%m.%Y'), self.headline)

    @classmethod
    def last(cls, *, count=1, offset=0, only_published=True, delivered=False, by_date=True):
        pushes = cls.objects.all()

        if only_published:
            pushes = pushes.filter(published=True)

        if not delivered:
            pushes = pushes.filter(delivered=False)

        if by_date:
            pushes = pushes.order_by('-pub_date')
        else:
            pushes = pushes.order_by('-id')

        return pushes[offset:count]

    def save(self, *args, **kwargs):
        if self.pk:
            queue.remove_scheduled("push.SendHighlight",
                                   {'push_id': self.pk},
                                   interval=HIGHLIGHT_CHECK_INTERVAL)

        super().save(*args, **kwargs)

        if self.published and not self.delivered:
            queue.add_scheduled("push.SendHighlight",
                                {'push_id': self.pk},
                                start_at=self.pub_date,
                                interval=HIGHLIGHT_CHECK_INTERVAL)


@receiver(pre_delete, sender=Push)
def push_delete_handler(sender, **kwargs):
    id = kwargs['instance'].pk
    queue.remove_scheduled("push.SendHighlight",
                           {'push_id': id},
                           interval=HIGHLIGHT_CHECK_INTERVAL)


class Category(models.Model):
    """
    Eine Meldung kann einer Kategorie zugeordnet werden.
    """

    class Meta:
        verbose_name = 'Kategorie'
        verbose_name_plural = 'Kategorien'
        ordering = ['-name']

    name = models.CharField('Name', max_length=200, null=False)

    def __str__(self):
        return self.name


class Report(models.Model):
    """
    Meldungen sind themenbezogene, in sich abgeschlossene Nachrichten.</p><p>
    Sie können aus mehreren Fragmenten bestehen. Um von einem Fragment zum nächsten zu gelangen,
    muss der Nutzer mit dem Bot interagieren, indem er einen Button mit einer weiterführenden Frage
    o.ä. anklickt.
    """

    class Meta:
        verbose_name = 'Meldung'
        verbose_name_plural = 'Meldungen'
        ordering = ['-created']

    headline = models.CharField('Überschrift', max_length=200, null=False)
    sport = models.CharField('Sportart', max_length=200, null=True, blank=True)
    discipline = models.CharField('Disziplin', max_length=200, null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Kategorie',
        related_name='reports', related_query_name='report'
    )
    text = models.CharField('Intro-Text', max_length=640, null=False)
    media = models.FileField('Medien-Anhang Intro', null=True, blank=True)
    attachment_id = models.CharField(
        'Facebook Attachment ID', max_length=64, null=True, blank=True,
        help_text="Wird automatisch ausgefüllt")

    created = models.DateTimeField(
        'Erstellt',
        default=timezone.now)

    published = models.BooleanField(
        'Freigegeben', null=False, default=False,
        help_text='Solange dieser Haken nicht gesetzt ist, wird diese Meldung nicht versendet, '
                  'weder in terminierten Highlight-Pushes noch an Abonnenten von bestimmten '
                  'Sportarten, Sportlern, Disziplinen etc.')

    delivered = models.BooleanField(
        'Versendet', null=False, default=False)

    def __str__(self):
        return '%s - %s' % (self.created.strftime('%d.%m.%Y'), self.headline)

    def update_attachment(self):
        if str(self.media):
            attachment_id = upload_attachment(self.media.url)
            self.attachment_id = attachment_id
        else:
            self.attachment_id = None

    @classmethod
    def last(cls, *, count=1, offset=0, only_published=True, delivered=False, by_date=True,
             ignore=None):
        reports = cls.objects.all()

        if only_published:
            reports = reports.filter(published=True)

        if not delivered:
            reports = reports.filter(delivered=False)

        if by_date:
            reports = reports.order_by('-created')
        else:
            reports = reports.order_by('-id')

        return reports.exclude(id__in=ignore or [])[offset:count]

    def save(self, *args, **kwargs):
        if self.pk:
            queue.remove_scheduled("push.SendReport",
                                   {'report_id': self.pk},
                                   interval=HIGHLIGHT_CHECK_INTERVAL)

        super().save(*args, **kwargs)

        if self.sport in supported_sports and self.published and not self.delivered:
            queue.add_scheduled("push.SendReport",
                                {'report_id': self.pk, 'sport': self.sport},
                                start_at=timezone.now() + timezone.timedelta(seconds=10),
                                interval=HIGHLIGHT_CHECK_INTERVAL)


class ReportFragment(models.Model):

    class Meta:
        verbose_name = 'Meldungs-Fragment'
        verbose_name_plural = 'Meldungs-Fragmente'

    report = models.ForeignKey('Report', on_delete=models.CASCADE, related_name='fragments',
                               related_query_name='fragment')

    question = models.CharField('Frage', max_length=20, null=False, blank=False)
    text = models.CharField('Text', max_length=640, null=False, blank=False)
    media = models.FileField('Medien-Anhang', null=True, blank=True)
    attachment_id = models.CharField(
        'Facebook Attachment ID', max_length=64, null=True, blank=True)

    def __str__(self):
        return '%s - %s' % (self.report.headline, self.question)

    def update_attachment(self):
        if str(self.media):
            attachment_id = upload_attachment(self.media.url)
            self.attachment_id = attachment_id
        else:
            self.attachment_id = None


class FacebookUser(models.Model):
    """
    Liste aller Abonnenten der Push-Benachrichtigungen.</p><p>
    Alle IDs sind seitenspezifisch und lassen
    sich nur für die Interaktion mit dem Sportsfreund nutzen.
    """

    class Meta:
        verbose_name = 'Facebook User'
        verbose_name_plural = 'Facebook User'

    uid = models.CharField('User ID', max_length=64, null=False, unique=True)
    state = models.CharField('State', max_length=64, null=True, blank=True)
    add_date = models.DateTimeField('Hinzugefügt am', default=timezone.now)

    def __str__(self):
        return str(self.uid)


class Wiki(models.Model):
    """
    Das Wiki ist ein Nachschlagewerk für kurze Erklärungen, das von Dialogflow gestützt wird.</p>
    <p>Wenn der Nutzer nach einem Begriff fragt, der in Dialogflow als wiki-Entity eingetragen ist,
    so wird der Wiki-Eintrag mit jenem <i>input</i> als Antwort gesendet.
    """

    class Meta:
        verbose_name = 'Wiki-Eintrag'
        verbose_name_plural = 'Wiki-Einträge'

    input = models.CharField('Eingabe', max_length=128, null=False, unique=True,
                             help_text="Der Eingabetext des Nutzers")
    output = models.CharField('Antwort', max_length=640, null=True, blank=True)
    media = models.FileField('Medien-Anhang', null=True, blank=True)
    attachment_id = models.CharField(
        'Facebook Attachment ID', max_length=64, null=True, blank=True)

    def update_attachment(self):
        if str(self.media):
            attachment_id = upload_attachment(self.media.url)
            self.attachment_id = attachment_id
        else:
            self.attachment_id = None

    def __str__(self):
        return self.input


class Info(models.Model):
    """"""
    class Meta:
        verbose_name = 'Info'
        verbose_name_plural = 'Infos'

    title = models.CharField('Titel', max_length=128, null=False, unique=True,
                             help_text="Hinweis: Wird nicht ausgespielt")
    content = models.CharField('Inhalt', max_length=600, null=True, blank=True,
                              help_text="Text der Info")
    media = models.FileField('Medien-Anhang', null=True, blank=True)
    attachment_id = models.CharField(
        'Facebook Attachment ID', max_length=64, null=True, blank=True)

    def update_attachment(self):
        if str(self.media):
            attachment_id = upload_attachment(self.media.url)
            self.attachment_id = attachment_id
        else:
            self.attachment_id = None

    def __str__(self):
        return self.title


class Story(models.Model):
    """
    Stories sind, ähnlich wie Wiki-Einträge, von Dialogflow gestützt. Sie bieten jedoch die
    Möglichkeit, ähnlich wie bei den Meldungen, über Fragmente mit Buttons einen Dialog mit dem
    Nutzer zu führen. Es kann außerdem in jedem Fragment ein Button zu einer anderen Story angelegt
    werden.</p><p>
    Zur Bezeichnung einer Story wird ein Slug generiert, welcher bestimmt, wie der Intent in
    Dialogflow heißen muss.</p><p>
    Beispiel: Eine Story namens <i>Hans im Glück</i> mit dem Slug <i>hans-im-gluck</i> wird
    von dem Intent <i>story:hans-im-gluck</i> aufgerufen.
    """

    class Meta:
        verbose_name = 'Story'
        verbose_name_plural = 'Stories'

    name = models.CharField('Name', max_length=200, null=False)
    slug = models.CharField('Slug', max_length=200, null=True, blank=True)
    text = models.CharField('Text', max_length=640, null=False)
    media = models.FileField('Medien-Anhang Intro', null=True, blank=True)
    attachment_id = models.CharField(
        'Facebook Attachment ID', max_length=64, null=True, blank=True)

    def __str__(self):
        return self.slug

    def _get_unique_slug(self):
        slug = slugify(self.name)
        unique_slug = slug
        num = 1
        while Story.objects.filter(slug=unique_slug).exists():
            unique_slug = '{}-{}'.format(slug, num)
            num += 1
        return unique_slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._get_unique_slug()
        super().save(*args, **kwargs)

    def update_attachment(self):
        if str(self.media):
            attachment_id = upload_attachment(self.media.url)
            self.attachment_id = attachment_id
        else:
            self.attachment_id = None


class StoryFragment(models.Model):

    class Meta:
        verbose_name = 'Story-Fragment'
        verbose_name_plural = 'Story-Fragmente'

    story = models.ForeignKey('Story', on_delete=models.CASCADE, related_name='fragments',
                              related_query_name='fragment')

    button = models.CharField('Button-Text', max_length=20, null=False, blank=False)
    text = models.CharField('Text', max_length=640, null=False, blank=False)
    media = models.FileField('Medien-Anhang', null=True, blank=True)
    link_story = models.ForeignKey('Story', on_delete=models.SET_NULL,
                                   related_name='+', related_query_name='+', null=True, blank=True)
    # link_url = models.CharField('Button zu URL', max_length=1024, null=True, blank=True)

    attachment_id = models.CharField(
        'Facebook Attachment ID', max_length=64, null=True, blank=True)

    def __str__(self):
        return '%s - %s' % (self.story.name, self.button)

    def update_attachment(self):
        if str(self.media):
            attachment_id = upload_attachment(self.media.url)
            self.attachment_id = attachment_id
        else:
            self.attachment_id = None
