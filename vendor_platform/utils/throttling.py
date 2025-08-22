from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class VendorThrottle(AnonRateThrottle):
    scope = 'vendor_registration'
    
class BookingThrottle(UserRateThrottle):
    scope = 'booking_creation'
    
class SearchThrottle(AnonRateThrottle):
    scope = 'search'