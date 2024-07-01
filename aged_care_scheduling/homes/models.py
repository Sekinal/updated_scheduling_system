from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()

class CareHome(models.Model):
    """
    Represents a Care Home entity in the system.

    This model stores information about care homes, including their
    name, address, contact details, manager, and capacity.
    """

    name = models.CharField(
        _("Name"),
        max_length=100,
        unique=True,
        help_text=_("The name of the care home")
    )
    address = models.TextField(
        _("Address"),
        help_text=_("The full address of the care home")
    )
    phone = models.CharField(
        _("Phone"),
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
            )
        ],
        help_text=_("Contact phone number for the care home")
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_homes',
        verbose_name=_("Manager"),
        help_text=_("The user responsible for managing this care home")
    )
    capacity = models.PositiveIntegerField(
        _("Capacity"),
        default=100,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(1000)
        ],
        help_text=_("Maximum number of residents the care home can accommodate")
    )
    created_at = models.DateTimeField(
        _("Created At"),
        default=timezone.now,
        help_text=_("Date and time when the care home was added to the system")
    )
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
        help_text=_("Date and time when the care home information was last updated")
    )
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("Designates whether this care home is active.")
    )

    class Meta:
        verbose_name = _("Care Home")
        verbose_name_plural = _("Care Homes")
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('care_home_detail', kwargs={'pk': self.pk})

    @property
    def is_at_capacity(self):
        """Check if the care home is at full capacity."""
        return self.residents.count() >= self.capacity

    def available_capacity(self):
        """Calculate the number of available spots in the care home."""
        return max(0, self.capacity - self.residents.count())