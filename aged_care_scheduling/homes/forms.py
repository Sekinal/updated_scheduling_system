from django import forms
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from .models import CareHome

class CareHomeForm(forms.ModelForm):
    """
    A form for creating and updating CareHome instances.
    
    This form includes custom validation, widget customization,
    and helper methods for improved usability and maintainability.
    """

    # Custom field for phone with regex validation
    phone = forms.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        widget=forms.TextInput(attrs={'placeholder': '+999999999'})
    )

    # Custom queryset for manager field
    manager = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(is_staff=True),
        empty_label="Select a manager",
        required=False
    )

    class Meta:
        model = CareHome
        fields = ['name', 'address', 'phone', 'manager', 'capacity']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter care home name'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter full address'}),
            'capacity': forms.NumberInput(attrs={'min': 1, 'max': 1000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'autofocus': True})

    def clean_name(self):
        """Custom validation for the name field."""
        name = self.cleaned_data.get('name')
        if CareHome.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A care home with this name already exists.")
        return name

    def clean(self):
        """Perform cross-field validation if needed."""
        cleaned_data = super().clean()
        # Add any cross-field validation here
        return cleaned_data

    def save(self, commit=True):
        """
        Override the save method to perform any additional operations
        before saving the instance.
        """
        instance = super().save(commit=False)
        # Perform any additional operations here
        if commit:
            instance.save()
        return instance