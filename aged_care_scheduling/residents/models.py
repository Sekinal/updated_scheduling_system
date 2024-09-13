# residents/models.py

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from homes.models import CareHome

class Resident(models.Model):
    first_name = models.CharField(_("First Name"), max_length=50)
    last_name = models.CharField(_("Last Name"), max_length=50)
    date_of_birth = models.DateField(_("Date of Birth"))
    care_home = models.ForeignKey(
        CareHome,
        on_delete=models.CASCADE,
        related_name='residents',
        verbose_name=_("Care Home")
    )
    admission_date = models.DateField(_("Admission Date"), null=True)
    emergency_email = models.EmailField(
        _("Emergency Contact Email"),
        null=True,
        blank=True
    )
    emergency_phone = models.CharField(
        _("Emergency Contact Phone"),
        max_length=20,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("Designates whether this resident is currently active in the care home.")
    )

    class Meta:
        verbose_name = _("Resident")
        verbose_name_plural = _("Residents")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def deactivate(self):
        """Deactivate the resident."""
        self.is_active = False
        self.save()

    def activate(self):
        """Activate the resident."""
        self.is_active = True
        self.save()