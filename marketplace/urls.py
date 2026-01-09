from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add/', views.add_parking_space, name='add_parking_space'),
    path('parking/<int:pk>/', views.parking_detail, name='parking_detail'),
    path('parking/<int:pk>/book/', views.book_parking_space, name='book_parking_space'),
    path('booking/<int:booking_id>/summary/', views.booking_summary, name='booking_summary'),
    
    # Host routes
    path('host/bookings/', views.host_bookings, name='host_bookings'),
    path('host/listings/<int:pk>/edit/', views.edit_parking_space, name='edit_parking_space'),
    path('host/listings/<int:pk>/archive/', views.toggle_archive_listing, name='toggle_archive_listing'),
    path('host/listings/<int:pk>/delete/', views.delete_parking_space, name='delete_parking_space'),
    path('host/bookings/<int:booking_id>/approve/', views.approve_booking, name='approve_booking'),
    path('host/bookings/<int:booking_id>/decline/', views.decline_booking, name='decline_booking'),
    
    # Renter routes
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('my-bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),

    # Authentication routes
    path("signup/", views.signup, name="signup"),
    path("verify/<uidb64>/<token>/", views.verify_email, name="verify_email"),

    path("login/", views.login_step_one, name="site_login"),
    path("login/code/", views.login_step_two, name="login_step_two"),
    path("verify/sent/", views.verification_sent, name="verification_sent"),

]
