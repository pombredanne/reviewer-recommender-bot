# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-29 15:39
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0006_change'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='change',
            options={'verbose_name': 'Change', 'verbose_name_plural': 'Changes'},
        ),
        migrations.RenameField(
            model_name='change',
            old_name='file',
            new_name='file_path',
        ),
    ]