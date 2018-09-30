# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-09-24 17:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0074_documentfield_require_text_annotations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentfieldvalue',
            name='location_end',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='documentfieldvalue',
            name='location_start',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicaldocumentfieldvalue',
            name='location_end',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicaldocumentfieldvalue',
            name='location_start',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
