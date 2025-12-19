from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def hello_parking(request):
    return HttpResponse("Hello Parking World!")
