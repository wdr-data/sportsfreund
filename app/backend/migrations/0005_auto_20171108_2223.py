# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-08 21:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_push_published'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='push',
            options={'verbose_name': 'Push', 'verbose_name_plural': 'Pushes'},
        ),
    ]