# Generated by Célia 23.8 on 2021-09-15 15:12

from django.apps import apps

from django.db import migrations


def merge_ratings_min_max(app, schema):
    site_model = apps.get_model('outdoor', 'Site')
    sites = site_model.objects.all()
    for site in sites:
        if hasattr(site, 'ratings_max') and hasattr(site, 'ratings_min'):
            for rating in site.ratings_max.all():
                site.ratings_min.add(rating)
            site.ratings_max.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('outdoor', '0024_auto_20210910_1002'),
    ]

    operations = [
        migrations.RunPython(merge_ratings_min_max, reverse_code=migrations.RunPython.noop),
    ]
