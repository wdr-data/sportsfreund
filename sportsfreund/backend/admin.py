from django.contrib import admin
from django import forms
from django.contrib import messages

from .models import Push, Report, ReportFragment, FacebookUser, Wiki, Info, Story, StoryFragment
from bot.fb import UploadFailedError


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

    attachment_id = forms.CharField(
        label='Facebook Attachment ID', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)

    delivered = forms.BooleanField(
        label='Versendet?',
        help_text="Wurde der Push bereits vom Bot versendet? Nur relevant für Breaking-News.",
        disabled=True,
        required=False)

    class Meta:
        model = Report
        fields = '__all__'


class ReportAdmin(admin.ModelAdmin):
    form = ReportModelForm
    date_hierarchy = 'created'
    list_filter = ['published']
    search_fields = ['headline']
    list_display = ('headline', 'created', 'published')
    inlines = (ReportFragmentAdminInline, )

    def save_model(self, request, obj, form, change):
        if 'media' in form.changed_data:
            try:
                obj.update_attachment()
            except UploadFailedError:
                messages.warning(request,
                                 "Upload von Facebook Attachment fehlgeschlagen: %s" % obj.media)

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        for form_ in formset.forms:
            if 'media' in form_.changed_data:
                try:
                    form_.instance.update_attachment()
                except UploadFailedError:
                    messages.warning(
                        request,
                        "Upload von Facebook Attachment fehlgeschlagen: %s" % form_.instance.media)

        super().save_formset(request, form, formset, change)


class PushModelForm(forms.ModelForm):
    text = forms.CharField(
        required=True, label="Intro-Text", widget=forms.Textarea, max_length=640)

    attachment_id = forms.CharField(
        label='Facebook Attachment ID', help_text="Wird automatisch ausgefüllt", disabled=True,
        required=False)

    delivered = forms.BooleanField(
        label='Versendet', help_text="Wurde dieser Push bereits versendet?", disabled=True,
        required=False)

    class Meta:
        model = Report
        fields = '__all__'


class PushAdmin(admin.ModelAdmin):
    form = PushModelForm
    date_hierarchy = 'pub_date'
    list_filter = ['published']
    search_fields = ['headline']
    list_display = ('headline', 'pub_date', 'published', 'delivered')


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
        if 'media' in form.changed_data:
            try:
                obj.update_attachment()
            except UploadFailedError:
                messages.warning(request,
                                 "Upload von Facebook Attachment fehlgeschlagen: %s" % obj.media)

        super().save_model(request, obj, form, change)


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
        if 'media' in form.changed_data:
            try:
                obj.update_attachment()
            except UploadFailedError:
                messages.warning(request,
                                 "Upload von Facebook Attachment fehlgeschlagen: %s" % obj.media)

        super().save_model(request, obj, form, change)


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
        model = Report
        fields = '__all__'


class StoryAdmin(admin.ModelAdmin):
    form = ReportModelForm
    search_fields = ['name', 'slug']
    list_display = ('name', 'slug')
    inlines = (ReportFragmentAdminInline, )

    def save_model(self, request, obj, form, change):
        if 'media' in form.changed_data:
            try:
                obj.update_attachment()
            except UploadFailedError:
                messages.warning(request,
                                 "Upload von Facebook Attachment fehlgeschlagen: %s" % obj.media)

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        for form_ in formset.forms:
            if 'media' in form_.changed_data:
                try:
                    form_.instance.update_attachment()
                except UploadFailedError:
                    messages.warning(
                        request,
                        "Upload von Facebook Attachment fehlgeschlagen: %s" % form_.instance.media)

        super().save_formset(request, form, formset, change)


# Register your models here.
admin.site.register(Push, PushAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(FacebookUser)
admin.site.register(Wiki, WikiAdmin)
admin.site.register(Info, InfoAdmin)
admin.site.register(Story, StoryAdmin)
