# Generated by Django 2.2.12 on 2020-05-15 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0009_auto_20200406_1356'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='is_image',
            field=models.BooleanField(db_index=True, default=False, editable=False, help_text='Is an image file', verbose_name='Is image'),
        ),
    ]
