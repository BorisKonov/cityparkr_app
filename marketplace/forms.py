from django import forms
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import requests
from .models import ParkingSpace, ParkingImage, Booking

class ParkingSpaceForm(forms.ModelForm):
    class Meta:
        model = ParkingSpace
        fields = ['title', 'description', 'location', 'price_per_hour']

    def clean_location(self):
        location = self.cleaned_data.get('location')
        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)

        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            return location

        base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": location,
            "key": api_key
        }

        try:
            response = requests.get(base_url, params=params)
            data = response.json()

            if data['status'] == 'OK':
                return location
            elif data['status'] == 'ZERO_RESULTS':
                raise forms.ValidationError("We couldn't find this location. Please check the address.")
            else:
                return location
        except requests.RequestException:
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
    class Meta:
        model = Booking
        fields = ['start_datetime', 'end_datetime']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'booking-date-input'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'booking-date-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.parking_space = kwargs.pop('parking_space', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')

        if not start_datetime:
             return cleaned_data

        # Check if start time is in the past
        if start_datetime < timezone.now():
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
