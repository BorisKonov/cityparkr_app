from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from .models import ParkingSpace
def hello_parking(request):
    return HttpResponse("Hello Parking World!")

def home(request):
    spaces = ParkingSpace.objects.all() #gets every parking space from the database
    return render(request, 'marketplace/home.html', {'spaces': spaces})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ParkingSpaceForm

@login_required
def add_parking_space(request):
    if request.method == 'POST':
        form = ParkingSpaceForm(request.POST)
        if form.is_valid():
            parking_space = form.save(commit=False)
            parking_space.owner = request.user
            parking_space.save()
            return redirect('home')
    else:
        form = ParkingSpaceForm()

    return render(request, 'marketplace/add_parking_space.html', {'form': form})