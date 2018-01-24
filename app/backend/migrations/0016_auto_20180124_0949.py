# Generated by Django 2.0.1 on 2018-01-24 08:49

from django.db import migrations
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0015_auto_20180122_1426'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='report',
            options={'ordering': ['-created'], 'verbose_name': 'Meldung', 'verbose_name_plural': 'Meldungen'},
        ),
        migrations.AlterField(
            model_name='push',
            name='reports',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='pushes', to='backend.Report', verbose_name='Meldungen'),
        ),
    ]
