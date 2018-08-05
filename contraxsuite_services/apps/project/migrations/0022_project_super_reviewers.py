# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-07-28 05:12
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0021_auto_20180725_1829'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='super_reviewers',
            field=models.ManyToManyField(blank=True, related_name='project_super_reviewers', to=settings.AUTH_USER_MODEL),
        ),
    ]
