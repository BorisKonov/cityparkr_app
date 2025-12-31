from django import forms
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import requests
from .models import ParkingSpace, ParkingImage, Booking
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# --- Custom Signup Form ---
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)
        field_classes = {'username': forms.CharField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Letters, digits and @/./+/-/_ only.'

# --- Custom DateTime Field for Quarter-Hour Selection ---

class CustomDateTimeWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = [
            forms.DateInput(attrs={'type': 'date', 'class': 'booking-date-input'}),
            forms.Select(attrs={'class': 'booking-time-input'}, choices=[(h, f'{h:02d}') for h in range(24)]),
            forms.Select(attrs={'class': 'booking-time-input'}, choices=[(m, f'{m:02d}') for m in [0, 15, 30, 45]]),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, datetime):
            return [value.date(), value.hour, value.minute]
        return [None, None, None]

class CustomDateTimeField(forms.MultiValueField):
    widget = CustomDateTimeWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateField(),
            forms.IntegerField(),
            forms.IntegerField(),
        )
        super().__init__(fields=fields, require_all_fields=True, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            # Combine date, hour, and minute into a single datetime object
            return datetime.combine(data_list[0], datetime.min.time()).replace(
                hour=data_list[1], minute=data_list[2]
            )
        return None

# --- Existing Forms ---

class ParkingSpaceForm(forms.ModelForm):
    class Meta:
        model = ParkingSpace
        fields = ['title', 'description', 'location', 'price_per_hour']

    def clean_location(self):
        location = self.cleaned_data.get('location')
        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)

        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            return location

        # ... (rest of the location validation)
        return location

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'multiple': True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class ParkingSpaceImageForm(forms.Form):
    images = MultipleFileField(label='Select images', required=True)

    def clean_images(self):
        images = self.files.getlist('images')
        if len(images) < 3:
            raise forms.ValidationError("You must upload at least 3 images.")
        return images

class BookingForm(forms.ModelForm):
    start_datetime = CustomDateTimeField(label="Start Time")
    end_datetime = CustomDateTimeField(label="End Time")

    class Meta:
        model = Booking
        fields = ['start_datetime', 'end_datetime']

    def __init__(self, *args, **kwargs):
        self.parking_space = kwargs.pop('parking_space', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')

        if not start_datetime:
             return cleaned_data

        # Make datetime timezone-aware before comparison
        aware_start_datetime = timezone.make_aware(start_datetime)

        if aware_start_datetime < timezone.now():
            raise forms.ValidationError("You cannot book a parking space in the past.")

        if not end_datetime:
             return cleaned_data

        if end_datetime <= start_datetime:
            raise forms.ValidationError("End time must be after start time.")

        # Conflict check
        if self.parking_space:
            conflicts = Booking.objects.filter(
                parking_space=self.parking_space,
                status='approved',
                start_datetime__lt=end_datetime,
                end_datetime__gt=start_datetime
            )
            if conflicts.exists():
                raise forms.ValidationError("This parking space is already booked for the selected dates.")

        return cleaned_data
