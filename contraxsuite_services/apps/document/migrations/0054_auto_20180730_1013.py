# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-07-30 10:13
from __future__ import unicode_literals

import apps.common.fields
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0053_custom_document_type_field_relation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentfield',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='documentfield',
            name='uid',
            field=apps.common.fields.StringUUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='documentfielddetector',
            name='extraction_hint',
            field=models.CharField(blank=True, choices=[('TAKE_FIRST', 'TAKE_FIRST'), ('TAKE_SECOND', 'TAKE_SECOND'), ('TAKE_LAST', 'TAKE_LAST'), ('TAKE_MIN', 'TAKE_MIN'), ('TAKE_MAX', 'TAKE_MAX'), ('ORDINAL_EXTRACTION_HINTS', 'ORDINAL_EXTRACTION_HINTS')], db_index=True, default='TAKE_FIRST', max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='documentfielddetector',
            name='uid',
            field=apps.common.fields.StringUUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='documentfieldvalue',
            name='extraction_hint',
            field=models.CharField(blank=True, choices=[('TAKE_FIRST', 'TAKE_FIRST'), ('TAKE_SECOND', 'TAKE_SECOND'), ('TAKE_LAST', 'TAKE_LAST'), ('TAKE_MIN', 'TAKE_MIN'), ('TAKE_MAX', 'TAKE_MAX'), ('ORDINAL_EXTRACTION_HINTS', 'ORDINAL_EXTRACTION_HINTS')], db_index=True, default='TAKE_FIRST', max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='documenttype',
            name='uid',
            field=apps.common.fields.StringUUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='historicaldocumentfieldvalue',
            name='extraction_hint',
            field=models.CharField(blank=True, choices=[('TAKE_FIRST', 'TAKE_FIRST'), ('TAKE_SECOND', 'TAKE_SECOND'), ('TAKE_LAST', 'TAKE_LAST'), ('TAKE_MIN', 'TAKE_MIN'), ('TAKE_MAX', 'TAKE_MAX'), ('ORDINAL_EXTRACTION_HINTS', 'ORDINAL_EXTRACTION_HINTS')], db_index=True, default='TAKE_FIRST', max_length=30, null=True),
        ),
    ]
