from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Vendor, VendorService, PricingTier, AvailabilitySlot
from utils.file_validation import FileSizeValidator, ImageDimensionValidator

class VendorRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    profile_image = serializers.ImageField(
        required=False,
        validators=[
            FileSizeValidator(limit_mb=5),
            ImageDimensionValidator(max_width=2000, max_height=2000)
        ]
    )
    
    class Meta:
        model = Vendor
        fields = [
            'email', 'password', 'company_name', 'description',
            'profile_image', 'address', 'city', 'state', 'country',
            'zip_code', 'phone', 'website'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        vendor = Vendor.objects.create_user(**validated_data)
        vendor.set_password(password)
        vendor.save()
        return vendor
        
class VendorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid credentials')
                
            if not user.is_active:
                raise serializers.ValidationError('Account is disabled')
                
            if user.status != 'approved':
                raise serializers.ValidationError('Vendor account not approved')
                
            data['user'] = user
            return data
            
        raise serializers.ValidationError('Email and password are required')
        
class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            'vendor_id', 'company_name', 'email', 'description',
            'profile_image', 'address', 'city', 'state', 'country',
            'zip_code', 'phone', 'website', 'rating', 'total_reviews',
            'status', 'created_at'
        ]
        read_only_fields = ['vendor_id', 'rating', 'total_reviews', 'status', 'created_at']
        
class PricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingTier
        fields = ['id', 'tier_name', 'description', 'price', 'min_quantity', 'max_quantity', 'is_active']
        
class VendorServiceSerializer(serializers.ModelSerializer):
    pricing_tiers = PricingTierSerializer(many=True, read_only=True)
    
    class Meta:
        model = VendorService
        fields = [
            'id', 'category', 'name', 'description', 'base_price', 
            'is_active', 'pricing_tiers', 'created_at'
        ]
        
class AvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySlot
        fields = [
            'id', 'service', 'date', 'start_time', 'end_time',
            'is_available', 'max_capacity', 'booked_capacity'
        ]
        
    def validate(self, data):
        # Check if end time is after start time
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError('End time must be after start time')
            
        # Check for overlapping slots
        vendor = data.get('vendor') or self.context.get('vendor')
        service = data.get('service')
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if all([vendor, service, date, start_time, end_time]):
            overlapping_slots = AvailabilitySlot.objects.filter(
                vendor=vendor,
                service=service,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if overlapping_slots.exists():
                raise serializers.ValidationError('Time slot overlaps with existing availability')
                
        return data