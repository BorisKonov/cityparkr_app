from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class ParkingSpace(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.location})"

class ParkingImage(models.Model):
    parking_space = models.ForeignKey(ParkingSpace, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='parking_images/')

    def __str__(self):
        return f"Image for {self.parking_space.title}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    ]

    DURATION_CHOICES = [
        ('hour', 'Hour'),
        ('day', 'Day'),
        ('month', 'Month'),
        ('year', 'Year'),
        ('forever', 'Forever'),
    ]

    parking_space = models.ForeignKey(ParkingSpace, related_name='bookings', on_delete=models.CASCADE)
    renter = models.ForeignKey(User, related_name='bookings', on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    duration_type = models.CharField(max_length=10, choices=DURATION_CHOICES, default='hour')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.duration_type == 'forever' and not self.end_datetime:
             # Set end_datetime to 10 years from start if 'forever' is chosen
             self.end_datetime = self.start_datetime + timedelta(days=365*10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.parking_space.title} - {self.renter.username} ({self.start_datetime.date()} to {self.end_datetime.date()})"
