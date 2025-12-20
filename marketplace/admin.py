from django.contrib import admin

# Register your models here.
from .models import ParkingSpace, Booking
admin.site.register(ParkingSpace)
admin.site.register(Booking)
