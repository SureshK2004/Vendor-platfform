from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from vendors import views as vendor_views
from bookings import views as booking_views
from search import views as search_views

router = routers.DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/register/', vendor_views.VendorRegistrationView.as_view(), name='vendor-register'),
    path('api/auth/login/', vendor_views.VendorLoginView.as_view(), name='vendor-login'),
    path('api/vendor/profile/', vendor_views.VendorProfileView.as_view(), name='vendor-profile'),
    path('api/vendor/services/', vendor_views.VendorServiceListView.as_view(), name='vendor-services'),
    path('api/vendor/services/<int:pk>/', vendor_views.VendorServiceDetailView.as_view(), name='vendor-service-detail'),
    path('api/vendor/availability/', vendor_views.AvailabilitySlotView.as_view(), name='vendor-availability'),
    path('api/vendor/bookings/', booking_views.VendorBookingListView.as_view(), name='vendor-bookings'),
    path('api/vendor/bookings/<int:pk>/', booking_views.VendorBookingDetailView.as_view(), name='vendor-booking-detail'),
    path('api/bookings/', booking_views.BookingCreateView.as_view(), name='create-booking'),
    path('api/search/vendors/', search_views.VendorSearchView.as_view(), name='vendor-search'),
]

urlpatterns += router.urls