from crispy_forms.layout import Div
from django.conf import settings
from django.forms.fields import CharField
from django.forms.widgets import HiddenInput, Textarea
from django.utils.translation import gettext_lazy as _

from geotrek.authent.models import SelectableUser
from geotrek.common.forms import CommonForm

from .models import Report


class ReportForm(CommonForm):
    geomfields = ["geom"]

    fieldslayout = [
        Div(
            "email",
            "comment",
            "activity",
            "category",
            "problem_magnitude",
            "related_trek",
            "status",
            "locked",
            "uid",
            "origin",
            "assigned_user"
        )
    ]

    class Meta:
        fields = [
            "geom",
            "email",
            "comment",
            "activity",
            "category",
            "problem_magnitude",
            "related_trek",
            "status",
            "locked",
            "uid",
            "origin",
            "assigned_user"
        ]
        model = Report

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if settings.SURICATE_MANAGEMENT_ENABLED:
            self.fields["assigned_user"].queryset = SelectableUser.objects.filter(userprofile__isnull=False)
            self.old_status_id = None
            self.fields["message"] = CharField(required=False)
            self.fields["message"].widget = Textarea()
            right_after_status_index = self.fieldslayout[0].fields.index('status') + 1
            self.fieldslayout[0].insert(right_after_status_index, 'message')
            if self.instance.pk:
                self.old_status_id = self.instance.status.suricate_id
                self.fields["status"].empty_label = None
                self.fields["status"].queryset = self.instance.next_status()
        else:
            self.fields["assigned_user"].widget = HiddenInput()

    def save(self, *args, **kwargs):
        report = super().save(self, *args, **kwargs)
        if self.instance.pk and settings.SURICATE_MANAGEMENT_ENABLED and 'status' in self.changed_data:
            msg = self.cleaned_data.get('message', "")
            report.send_notifications_on_status_change(self.old_status_id, msg)
        return report
