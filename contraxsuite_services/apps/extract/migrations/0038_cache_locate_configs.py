# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-01 14:33
from __future__ import unicode_literals

from django.db import migrations

from apps.common.advancedcelery.db_cache import DbCache


class Migration(migrations.Migration):
    dependencies = [
        ('extract', '0037_geoentity_priority'),
    ]

    operations = [
        migrations.RunPython(DbCache.cache_court_config),
        migrations.RunPython(DbCache.cache_geo_config),
        migrations.RunPython(DbCache.cache_term_stems),
    ]
