# Generated by Django 4.2.13 on 2024-05-29 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0042_alter_report_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='provider',
            field=models.CharField(blank=True, db_index=True, max_length=1024, verbose_name='Provider'),
        ),
    ]
