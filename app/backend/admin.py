from django.contrib import admin, messages
from django import forms
from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple

from .models import (Push, Report, ReportFragment, FacebookUser, Wiki, Info, Story, StoryFragment,
                     Category)
from feeds.config import SPORTS_CONFIG
from lib.facebook import UploadFailedError

SPORT_NAMES = tuple(sorted(s.name for s in SPORTS_CONFIG))

DISCIPLINE_NAMES = []

for sport in SPORTS_CONFIG:
    DISCIPLINE_NAMES.extend(d.name for d in sport.disciplines)

DISCIPLINE_NAMES = tuple(sorted(set(DISCIPLINE_NAMES)))

EMPTY_CHOICE = ((None, '---------'), )

UPLOAD_FAILED_MSG = 'Die Datei "%s" konnte nicht zu Facebook hochgeladen werden. ' \
                    'Bitte versuche es erneut.'


class ReportFragmentModelForm(forms.ModelForm):
    text = forms.CharField(
        required=True, label="Text", widget=forms.Textarea, max_length=640)

    attachment_id = forms.CharField(
        label='Facebook Attachment ID', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)

    class Meta:
        model = ReportFragment
        fields = '__all__'


class ReportFragmentAdmin(admin.ModelAdmin):
    form = ReportFragmentModelForm


class ReportFragmentAdminInline(admin.TabularInline):
    model = ReportFragment
    form = ReportFragmentModelForm


class ReportModelForm(forms.ModelForm):
    text = forms.CharField(
        required=True, label="Intro-Text", widget=forms.Textarea, max_length=640)

    sport = forms.CharField(
        required=False,
        widget=forms.Select(choices=EMPTY_CHOICE + tuple((s, s) for s in SPORT_NAMES)))

    discipline = forms.CharField(
        required=False,
        widget=forms.Select(choices=EMPTY_CHOICE + tuple((s, s) for s in DISCIPLINE_NAMES)))

    attachment_id = forms.CharField(
        label='Facebook Attachment ID', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)

    delivered = forms.BooleanField(
        label='Versendet',
        help_text="Wurde diese Meldung bereits in einem Highlights-Push vom Bot versendet?",
        disabled=True,
        required=False)

    class Meta:
        model = Report
        fields = ('headline', 'sport', 'discipline', 'category',
                  'text', 'media', 'attachment_id', 'published', 'delivered')


class ReportAdmin(admin.ModelAdmin):
    form = ReportModelForm
    date_hierarchy = 'created'
    list_filter = ['published', 'category']
    search_fields = ['headline']
    list_display = ('headline', 'category', 'created', 'published')
    inlines = (ReportFragmentAdminInline, )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if 'media' in form.changed_data:
            try:
                obj.update_attachment()
                form.changed_data = ['attachment_id']
                super().save_model(request, obj, form, change)

            except UploadFailedError:
                messages.error(request, UPLOAD_FAILED_MSG % obj.media)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)

        for form_ in formset.forms:
            if 'media' in form_.changed_data:
                try:
                    form_.instance.update_attachment()
                    form.changed_data = ['attachment_id']
                    super().save_formset(request, form, formset, change)

                except UploadFailedError:
                    messages.error(request, UPLOAD_FAILED_MSG % form_.instance.media)


class PushModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reports'].queryset = Report.objects.order_by('-created')

    text = forms.CharField(
        required=True, label="Intro-Text", widget=forms.Textarea, max_length=640)

    delivered = forms.BooleanField(
        label='Versendet', help_text="Wurde dieser Push bereits versendet?", disabled=True,
        required=False)

    outro = forms.CharField(
        required=True, label="Outro-Text",
        widget=forms.Textarea, initial="Das war's für den Moment. Bis dann.", max_length=640)

    class Meta:
        model = Push
        fields = '__all__'


class PushAdmin(admin.ModelAdmin):
    form = PushModelForm
    date_hierarchy = 'pub_date'
    list_filter = ['published']
    search_fields = ['headline']
    list_display = ('published', 'pub_date', 'headline',  'delivered')
    list_display_links = ('pub_date',)
    ordering = ('-pub_date',)
    readonly_fields = ('attachment_id_intro', 'attachment_id_outro')

    # filter_horizontal = ('reports', )

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in ('reports', ):
            kwargs['widget'] = SortedFilteredSelectMultiple(
                attrs={'verbose_name': db_field.verbose_name})
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        changed_data = []

        if 'media_intro' in form.changed_data:
            try:
                obj.update_attachment_intro()
                changed_data.append('attachment_id_intro')

            except UploadFailedError:
                messages.error(request, UPLOAD_FAILED_MSG % obj.media_intro)

        if 'media_outro' in form.changed_data:
            try:
                obj.update_attachment_outro()
                changed_data.append('attachment_id_outro')

            except UploadFailedError:
                messages.error(request, UPLOAD_FAILED_MSG % obj.media_outro)

        if changed_data:
            form.changed_data = changed_data
            super().save_model(request, obj, form, change)


class WikiModelForm(forms.ModelForm):
    output = forms.CharField(
        required=True, label="Antwort", widget=forms.Textarea, max_length=640,
        help_text="Die Antwort, die der Bot auf die Eingabe geben soll")

    class Meta:
        model = Wiki
        fields = '__all__'


class WikiAdmin(admin.ModelAdmin):
    form = WikiModelForm
    search_fields = ['input']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if 'media' in form.changed_data:
            try:
                obj.update_attachment()
                form.changed_data = ['attachment_id']
                super().save_model(request, obj, form, change)

            except UploadFailedError:
                messages.error(request, UPLOAD_FAILED_MSG % obj.media)


class InfoModelForm(forms.ModelForm):
    content = forms.CharField(
        required=True, label="Inhalt", widget=forms.Textarea, max_length=600)

    class Meta:
        model = Info
        fields = '__all__'


class InfoAdmin(admin.ModelAdmin):
    form = InfoModelForm
    search_fields = ['title']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if 'media' in form.changed_data:
            try:
                obj.update_attachment()
                form.changed_data = ['attachment_id']
                super().save_model(request, obj, form, change)

            except UploadFailedError:
                messages.error(request, UPLOAD_FAILED_MSG % obj.media)


class StoryFragmentModelForm(forms.ModelForm):
    text = forms.CharField(
        required=True, label="Text", widget=forms.Textarea, max_length=640)

    attachment_id = forms.CharField(
        label='Facebook Attachment ID', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)

    class Meta:
        model = StoryFragment
        fields = '__all__'


class StoryFragmentAdmin(admin.ModelAdmin):
    form = StoryFragmentModelForm


class StoryFragmentAdminInline(admin.TabularInline):
    model = StoryFragment
    form = StoryFragmentModelForm
    fk_name = 'story'


class StoryModelForm(forms.ModelForm):
    text = forms.CharField(
        required=True, label="Text", widget=forms.Textarea, max_length=640)

    slug = forms.CharField(
        label='Slug', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)

    attachment_id = forms.CharField(
        label='Facebook Attachment ID', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)

    class Meta:
        model = Story
        fields = '__all__'


class StoryAdmin(admin.ModelAdmin):
    form = StoryModelForm
    search_fields = ['name', 'slug']
    list_display = ('name', 'slug')
    inlines = (StoryFragmentAdminInline, )
    ordering = ('slug',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if 'media' in form.changed_data:
            try:
                obj.update_attachment()
                form.changed_data = ['attachment_id']
                super().save_model(request, obj, form, change)

            except UploadFailedError:
                messages.error(request, UPLOAD_FAILED_MSG % obj.media)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)

        for form_ in formset.forms:
            if 'media' in form_.changed_data:
                try:
                    form_.instance.update_attachment()
                    form.changed_data = ['attachment_id']
                    super().save_formset(request, form, formset, change)

                except UploadFailedError:
                    messages.error(request, UPLOAD_FAILED_MSG % form_.instance.media)


# Register your models here.
admin.site.register(Push, PushAdmin)
admin.site.register(Category)
admin.site.register(Report, ReportAdmin)
admin.site.register(FacebookUser)
admin.site.register(Wiki, WikiAdmin)
admin.site.register(Info, InfoAdmin)
admin.site.register(Story, StoryAdmin)
