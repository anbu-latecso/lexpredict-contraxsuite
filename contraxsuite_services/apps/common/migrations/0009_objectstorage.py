# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-08-09 19:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from apps.task.tasks import Locate


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0008_migrate_groups_20180713_1351'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObjectStorage',
            fields=[
                ('key', models.CharField(db_index=True, max_length=100, primary_key=True, serialize=False)),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('data', models.BinaryField(blank=True, null=True)),
            ],
        )
    ]
