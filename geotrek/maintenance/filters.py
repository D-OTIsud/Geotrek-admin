from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django_filters import ChoiceFilter

from mapentity.filters import PolygonFilter, PythonPolygonFilter

from geotrek.core.models import Topology
from geotrek.common.filters import (
    StructureRelatedFilterSet, YearFilter, YearBetweenFilter)
from geotrek.common.widgets import YearSelect

from .models import Intervention, Project

if 'geotrek.signage' in settings.INSTALLED_APPS:
    from geotrek.signage.models import Blade


class InterventionYearTargetFilter(YearFilter):
    def do_filter(self, qs, year):
        interventions = Intervention.objects.filter(date__year=year).values_list('target_id', flat=True)
        return qs.filter(**{
            'id__in': interventions
        }).distinct()


class PolygonTopologyFilter(PolygonFilter):
    def filter(self, qs, value):
        if not value:
            return qs
        lookup = self.lookup_expr

        inner_qs = list(Topology.objects.filter(**{'geom__%s' % lookup: value}).values_list('id', flat=True))
        if 'geotrek.signage' in settings.INSTALLED_APPS:
            inner_qs.extend(Blade.objects.filter(**{'signage__geom__%s' % lookup: value}).values_list('id', flat=True))
        qs = qs.filter(**{'target_id__in': inner_qs})
        return qs


class InterventionYearSelect(YearSelect):
    label = _("Year")

    def get_years(self):
        return Intervention.objects.all_years()


class InterventionFilterSet(StructureRelatedFilterSet):
    ON_CHOICES = (('infrastructure', _("Infrastructure")), ('signage', _("Signage")), ('blade', _("Blade")),
                  ('topology', _("Path")), ('trek', _("Trek")), ('poi', _("POI")), ('service', _("Service")),
                  ('trail', _("Trail")))
    bbox = PolygonTopologyFilter(lookup_expr='intersects')
    year = YearFilter(field_name='date',
                      widget=InterventionYearSelect,
                      label=_("Year"))
    on = ChoiceFilter(field_name='target_type__model', choices=ON_CHOICES, label=_("On"), empty_label=_("On"))

    class Meta(StructureRelatedFilterSet.Meta):
        model = Intervention
        fields = StructureRelatedFilterSet.Meta.fields + [
            'status', 'type', 'stake', 'subcontracting', 'project', 'on',
        ]


class ProjectYearSelect(YearSelect):
    label = _("Year of activity")

    def get_years(self):
        return Project.objects.all_years()


class ProjectFilterSet(StructureRelatedFilterSet):
    bbox = PythonPolygonFilter(field_name='geom')
    in_year = YearBetweenFilter(field_name=('begin_year', 'end_year'),
                                widget=ProjectYearSelect,
                                label=_("Year of activity"))

    class Meta(StructureRelatedFilterSet.Meta):
        model = Project
        fields = StructureRelatedFilterSet.Meta.fields + [
            'in_year', 'type', 'domain', 'contractors', 'project_owner',
            'project_manager', 'founders'
        ]
