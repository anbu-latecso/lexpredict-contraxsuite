# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-07-26 07:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0051_auto_20180718_0713'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentfield',
            name='description',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
