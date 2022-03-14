# Generated by Django 3.1.14 on 2022-03-14 11:46

from django.conf import settings
from django.db import migrations


def forward(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for lang in settings.MODELTRANSLATION_LANGUAGES:
            cursor.execute(
                f"ALTER TABLE infrastructure_infrastructure ALTER COLUMN published_{lang} SET DEFAULT FALSE;"
            )
            cursor.execute(
                f"UPDATE infrastructure_infrastructure SET published_{lang} = False WHERE published = False;  "
            )


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0028_infrastructure_published_translation'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
