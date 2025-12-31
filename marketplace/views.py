from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ParkingSpace, ParkingImage, Booking
from .forms import ParkingSpaceForm, ParkingSpaceImageForm, BookingForm

def hello_parking(request):
    return HttpResponse("Hello Parking World!")

def home(request):
    spaces = ParkingSpace.objects.all()
    return render(request, 'marketplace/home.html', {'spaces': spaces})

def parking_detail(request, pk):
    space = get_object_or_404(ParkingSpace, pk=pk)
    booking_form = BookingForm()
    return render(request, 'marketplace/parking_detail.html', {
        'space': space,
        'booking_form': booking_form
    })

@login_required
def book_parking_space(request, pk):
    space = get_object_or_404(ParkingSpace, pk=pk)
    if request.method == 'POST':
        form = BookingForm(request.POST, parking_space=space)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.renter = request.user
            booking.parking_space = space
            booking.status = 'pending'
            booking.save()
            # Redirect to summary page instead of detail page
            return redirect('booking_summary', booking_id=booking.pk)
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            return render(request, 'marketplace/parking_detail.html', {
                'space': space,
                'booking_form': form
            })
    return redirect('parking_detail', pk=pk)

@login_required
def booking_summary(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, renter=request.user)
    return render(request, 'marketplace/booking_summary.html', {'booking': booking})

@login_required
def add_parking_space(request):
    if request.method == 'POST':
        form = ParkingSpaceForm(request.POST)
        image_form = ParkingSpaceImageForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            parking_space = form.save(commit=False)
            parking_space.owner = request.user
            parking_space.save()

            for image in request.FILES.getlist('images'):
                ParkingImage.objects.create(parking_space=parking_space, image=image)

            return redirect('home')
    else:
        form = ParkingSpaceForm()
        image_form = ParkingSpaceImageForm()

    return render(request, 'marketplace/add_parking_space.html', {'form': form, 'image_form': image_form})

@login_required
def host_bookings(request):
    # Get bookings for spaces owned by the current user
    bookings = Booking.objects.filter(parking_space__owner=request.user).order_by('status', '-created_at')
    return render(request, 'marketplace/host_bookings.html', {'bookings': bookings})

@login_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, parking_space__owner=request.user)
    
    # Re-check conflicts before approving
    conflicts = Booking.objects.filter(
        parking_space=booking.parking_space,
        status='approved',
        start_datetime__lt=booking.end_datetime,
        end_datetime__gt=booking.start_datetime
    ).exclude(pk=booking.pk)
    
    if conflicts.exists():
        messages.error(request, "Cannot approve: Conflict with another approved booking.")
    else:
        booking.status = 'approved'
        booking.save()
        messages.success(request, "Booking approved.")
        
    return redirect('host_bookings')

@login_required
def decline_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, parking_space__owner=request.user)
    booking.status = 'declined'
    booking.save()
    messages.success(request, "Booking declined.")
    return redirect('host_bookings')

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(renter=request.user).order_by('-created_at')
    return render(request, 'marketplace/my_bookings.html', {'bookings': bookings})
