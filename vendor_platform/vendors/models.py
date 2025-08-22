from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import os

# -------------------------------
# Utility Functions / Validators
# -------------------------------

def vendor_image_upload_path(instance, filename):
    """Generate unique file path for vendor profile images."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('vendors', filename)

def FileSizeValidator(limit_mb):
    """Factory function for validating max file size."""
    def validator(file):
        if file.size > limit_mb * 1024 * 1024:
            raise ValidationError(f"Maximum file size is {limit_mb} MB")
    return validator

# -------------------------------
# Vendor Model
# -------------------------------

class Vendor(AbstractUser):
    VENDOR_STATUS = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('suspended', 'Suspended'),
        ('rejected', 'Rejected'),
    )

    vendor_id = models.CharField(max_length=20, unique=True, editable=False)
    company_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    profile_image = models.ImageField(
        upload_to=vendor_image_upload_path,
        null=True,
        blank=True,
        validators=[FileSizeValidator(5)]  # 5 MB max
    )
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=VENDOR_STATUS, default='pending')
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_reviews = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Override username field to use email instead
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['company_name']

    def save(self, *args, **kwargs):
        if not self.vendor_id:
            self.vendor_id = self.generate_vendor_id()
        super().save(*args, **kwargs)

    def generate_vendor_id(self):
        return f"V{str(timezone.now().timestamp()).replace('.', '')[-8:]}"

    def __str__(self):
        return self.company_name

    class Meta:
        db_table = 'vendors'
        indexes = [
            models.Index(fields=['status', 'rating']),
            models.Index(fields=['city', 'state']),
        ]

# -------------------------------
# Vendor Service Category
# -------------------------------

class VendorServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'vendor_service_categories'
        verbose_name_plural = 'Vendor Service Categories'

# -------------------------------
# Vendor Service
# -------------------------------

class VendorService(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(VendorServiceCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vendor.company_name} - {self.name}"

    class Meta:
        db_table = 'vendor_services'
        unique_together = ['vendor', 'name']

# -------------------------------
# Pricing Tier
# -------------------------------

class PricingTier(models.Model):
    service = models.ForeignKey(VendorService, on_delete=models.CASCADE, related_name='pricing_tiers')
    tier_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    min_quantity = models.PositiveIntegerField(default=1)
    max_quantity = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'pricing_tiers'
        ordering = ['min_quantity']

    def __str__(self):
        return f"{self.service.name} - {self.tier_name}"

# -------------------------------
# Availability Slot
# -------------------------------

class AvailabilitySlot(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='availability_slots')
    service = models.ForeignKey(VendorService, on_delete=models.CASCADE, related_name='availability_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    max_capacity = models.PositiveIntegerField(default=1)
    booked_capacity = models.PositiveIntegerField(default=0)

    def is_fully_booked(self):
        return not self.is_available or self.booked_capacity >= self.max_capacity

    def __str__(self):
        return f"{self.vendor.company_name} - {self.service.name} on {self.date} ({self.start_time} - {self.end_time})"

    class Meta:
        db_table = 'availability_slots'
        unique_together = ['vendor', 'service', 'date', 'start_time']
        indexes = [
            models.Index(fields=['date', 'is_available']),
        ]
