from django.urls import path
from . import views
urlpatterns = [
    path('', views.hello_parking, name='hello_parking'),
]