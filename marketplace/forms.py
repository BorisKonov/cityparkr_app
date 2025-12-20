from django import forms
from .models import ParkingSpace

class ParkingSpaceForm(forms.ModelForm):
    class Meta:
        model = ParkingSpace
        fields = ['title', 'description', 'location', 'price_per_hour']