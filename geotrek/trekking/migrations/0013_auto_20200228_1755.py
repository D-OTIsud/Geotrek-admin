# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2020-02-28 16:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trekking', '0012_auto_20200211_1011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accessibility',
            name='pictogram',
            field=models.FileField(blank=True, max_length=512, null=True, upload_to='upload', verbose_name='Pictogram'),
        ),
        migrations.AlterField(
            model_name='difficultylevel',
            name='pictogram',
            field=models.FileField(blank=True, max_length=512, null=True, upload_to='upload', verbose_name='Pictogram'),
        ),
        migrations.AlterField(
            model_name='poi',
            name='name',
            field=models.CharField(help_text='Public name (Change carefully)', max_length=128, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='poi',
            name='publication_date',
            field=models.DateField(blank=True, editable=False, null=True, verbose_name='Publication date'),
        ),
        migrations.AlterField(
            model_name='poi',
            name='published',
            field=models.BooleanField(default=False, help_text='Online', verbose_name='Published'),
        ),
        migrations.AlterField(
            model_name='poi',
            name='review',
            field=models.BooleanField(default=False, verbose_name='Waiting for publication'),
        ),
        migrations.AlterField(
            model_name='poitype',
            name='pictogram',
            field=models.FileField(max_length=512, null=True, upload_to='upload', verbose_name='Pictogram'),
        ),
        migrations.AlterField(
            model_name='practice',
            name='pictogram',
            field=models.FileField(max_length=512, null=True, upload_to='upload', verbose_name='Pictogram'),
        ),
        migrations.AlterField(
            model_name='route',
            name='pictogram',
            field=models.FileField(blank=True, max_length=512, null=True, upload_to='upload', verbose_name='Pictogram'),
        ),
        migrations.AlterField(
            model_name='servicetype',
            name='name',
            field=models.CharField(help_text='Public name (Change carefully)', max_length=128, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='servicetype',
            name='pictogram',
            field=models.FileField(max_length=512, null=True, upload_to='upload', verbose_name='Pictogram'),
        ),
        migrations.AlterField(
            model_name='servicetype',
            name='publication_date',
            field=models.DateField(blank=True, editable=False, null=True, verbose_name='Publication date'),
        ),
        migrations.AlterField(
            model_name='servicetype',
            name='published',
            field=models.BooleanField(default=False, help_text='Online', verbose_name='Published'),
        ),
        migrations.AlterField(
            model_name='servicetype',
            name='review',
            field=models.BooleanField(default=False, verbose_name='Waiting for publication'),
        ),
        migrations.AlterField(
            model_name='trek',
            name='name',
            field=models.CharField(help_text='Public name (Change carefully)', max_length=128, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='trek',
            name='publication_date',
            field=models.DateField(blank=True, editable=False, null=True, verbose_name='Publication date'),
        ),
        migrations.AlterField(
            model_name='trek',
            name='published',
            field=models.BooleanField(default=False, help_text='Online', verbose_name='Published'),
        ),
        migrations.AlterField(
            model_name='trek',
            name='review',
            field=models.BooleanField(default=False, verbose_name='Waiting for publication'),
        ),
        migrations.AlterField(
            model_name='treknetwork',
            name='pictogram',
            field=models.FileField(max_length=512, null=True, upload_to='upload', verbose_name='Pictogram'),
        ),
        migrations.AlterField(
            model_name='weblinkcategory',
            name='pictogram',
            field=models.FileField(max_length=512, null=True, upload_to='upload', verbose_name='Pictogram'),
        ),
    ]