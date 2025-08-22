from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid

class Booking(models.Model):
    BOOKING_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    booking_id = models.CharField(max_length=20, unique=True, editable=False)
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.PROTECT, related_name='bookings')
    service = models.ForeignKey('vendors.VendorService', on_delete=models.PROTECT, related_name='bookings')
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    special_requests = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = self.generate_booking_id()
        super().save(*args, **kwargs)
    
    def generate_booking_id(self):
        return f"B{str(timezone.now().timestamp()).replace('.', '')[-10:]}"
    
    class Meta:
        db_table = 'bookings'
        indexes = [
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['booking_date', 'status']),
        ]
        
class BookingHistory(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20, choices=Booking.BOOKING_STATUS)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('vendors.Vendor', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'booking_history'
        ordering = ['-created_at']