# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-08-02 06:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0057_merge_20180802_0716'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentfield',
            name='value_regexp',
            field=models.TextField(blank=True, null=True),
        ),
    ]
