from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import ParkingSpace, ParkingImage, Booking
from .forms import ParkingSpaceForm, ParkingSpaceImageForm, BookingForm, CustomUserCreationForm
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
import random

def custom_logout(request):
    logout(request)
    return redirect('home')

def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            verify_url = request.build_absolute_uri(
                reverse("verify_email", kwargs={"uidb64": uid, "token": token})
            )

            send_mail(
                subject="Verify your CityParkr email",
                message=f"Hi {user.username},\n\nVerify your email by clicking:\n{verify_url}\n\nIf you did not create this account, ignore this email.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email],
            )

            request.session["pending_verification_email"] = user.email
            return redirect("verification_sent")

    else:
        form = CustomUserCreationForm()

    return render(request, "registration/signup.html", {"form": form})

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verified! You can now log in.")
        return redirect("site_login")

    messages.error(request, "Verification link is invalid or expired.")
    return redirect("signup")

def login_step_one(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if not user.is_active:
                messages.error(request, "You must verify your email before logging in.")
                return redirect("login")

            code = "".join([str(random.randint(0, 9)) for _ in range(6)])

            request.session["pending_2fa_user_id"] = user.id
            request.session["pending_2fa_code"] = code

            send_mail(
                subject="Your CityParkr login code",
                message=f"Your login code is: {code}\n\nIf you did not try to log in, please change your password.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email],
            )

            return redirect("login_step_two")
    else:
        form = AuthenticationForm(request)

    return render(request, "registration/login.html", {"form": form})

def login_step_two(request):
    if "pending_2fa_user_id" not in request.session:
        return redirect("login")

    if request.method == "POST":
        entered = request.POST.get("code", "").strip()
        real = request.session.get("pending_2fa_code")

        if entered == real:
            user_id = request.session["pending_2fa_user_id"]
            user = User.objects.get(id=user_id)

            request.session.pop("pending_2fa_user_id", None)
            request.session.pop("pending_2fa_code", None)

            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect("home")

        messages.error(request, "Invalid code. Please try again.")

    return render(request, "registration/two_factor.html")

def verification_sent(request):
    email = request.session.get("pending_verification_email", "")
    return render(request, "registration/verification_sent.html", {"email": email})

def hello_parking(request):
    return HttpResponse("Hello Parking World!")

def home(request):
    # Only show available spaces
    spaces = ParkingSpace.objects.filter(is_available=True)
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
def edit_parking_space(request, pk):
    space = get_object_or_404(ParkingSpace, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ParkingSpaceForm(request.POST, instance=space)
        # We don't handle image editing in this simple version, just details
        if form.is_valid():
            form.save()
            messages.success(request, "Listing updated successfully.")
            return redirect('host_bookings')
    else:
        form = ParkingSpaceForm(instance=space)
    
    return render(request, 'marketplace/edit_parking_space.html', {'form': form, 'space': space})

@login_required
def toggle_archive_listing(request, pk):
    space = get_object_or_404(ParkingSpace, pk=pk, owner=request.user)
    if request.method == 'POST':
        space.is_available = not space.is_available
        space.save()
        status = "Active" if space.is_available else "Archived"
        messages.success(request, f"Listing is now {status}.")
    return redirect('host_bookings')

@login_required
def host_bookings(request):
    # Get bookings for spaces owned by the current user
    bookings = Booking.objects.filter(parking_space__owner=request.user).order_by('status', '-created_at')
    # Also get the user's listings to manage them
    my_listings = ParkingSpace.objects.filter(owner=request.user)
    return render(request, 'marketplace/host_bookings.html', {'bookings': bookings, 'my_listings': my_listings})

@login_required
def delete_parking_space(request, pk):
    space = get_object_or_404(ParkingSpace, pk=pk, owner=request.user)
    if request.method == 'POST':
        space.delete()
        messages.success(request, "Listing deleted successfully.")
    return redirect('host_bookings')

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

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, renter=request.user)
    if booking.status == 'pending':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, "Booking request cancelled.")
    else:
        messages.error(request, "Cannot cancel this booking.")
    return redirect('my_bookings')
