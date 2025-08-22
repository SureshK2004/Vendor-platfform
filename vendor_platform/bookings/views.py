from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from django.conf import settings
from datetime import datetime

from .models import Booking, BookingHistory
from vendors.models import AvailabilitySlot, VendorService
from .serializers import BookingSerializer, BookingCreateSerializer
from utils.pricing import calculate_total_price

class BookingCreateView(APIView):
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Validate availability
                    service = VendorService.objects.get(
                        id=serializer.validated_data['service_id'],
                        is_active=True
                    )
                    
                    # Check if slot is available
                    slot = AvailabilitySlot.objects.select_for_update().get(
                        id=serializer.validated_data['slot_id'],
                        is_available=True
                    )
                    
                    if slot.is_fully_booked():
                        return Response(
                            {'error': 'Time slot is fully booked'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Calculate pricing
                    pricing_data = calculate_total_price(
                        service, 
                        serializer.validated_data['quantity'],
                        serializer.validated_data.get('pricing_tier_id')
                    )
                    
                    # Create booking
                    booking = Booking.objects.create(
                        vendor=service.vendor,
                        service=service,
                        customer_name=serializer.validated_data['customer_name'],
                        customer_email=serializer.validated_data['customer_email'],
                        customer_phone=serializer.validated_data.get('customer_phone', ''),
                        booking_date=slot.date,
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        quantity=serializer.validated_data['quantity'],
                        base_price=pricing_data['base_price'],
                        tax_amount=pricing_data['tax_amount'],
                        platform_fee=pricing_data['platform_fee'],
                        total_amount=pricing_data['total_amount'],
                        special_requests=serializer.validated_data.get('special_requests', '')
                    )
                    
                    # Update slot capacity
                    slot.booked_capacity += 1
                    slot.save()
                    
                    # Create booking history
                    BookingHistory.objects.create(
                        booking=booking,
                        status='pending',
                        notes='Booking created'
                    )
                    
                    # Send confirmation email (mock implementation)
                    self.send_confirmation_email(booking)
                    
                    return Response(
                        BookingSerializer(booking).data,
                        status=status.HTTP_201_CREATED
                    )
                    
            except VendorService.DoesNotExist:
                return Response(
                    {'error': 'Service not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except AvailabilitySlot.DoesNotExist:
                return Response(
                    {'error': 'Time slot not available'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def send_confirmation_email(self, booking):
        # In a real implementation, you would use Django's email system
        # or a service like SendGrid/Mailgun
        print(f"Mock email sent to {booking.customer_email}")
        print(f"Booking confirmed: {booking.booking_id}")
        
class VendorBookingListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(cache_page(60 * 2))  # Cache for 2 minutes
    def get(self, request):
        status_filter = request.query_params.get('status')
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        
        bookings = Booking.objects.filter(vendor=request.user)
        
        if status_filter:
            bookings = bookings.filter(status=status_filter)
            
        if date_from:
            bookings = bookings.filter(booking_date__gte=date_from)
            
        if date_to:
            bookings = bookings.filter(booking_date__lte=date_to)
            
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
        
class VendorBookingDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self, pk, vendor):
        try:
            return Booking.objects.get(pk=pk, vendor=vendor)
        except Booking.DoesNotExist:
            return None
            
    def get(self, request, pk):
        booking = self.get_object(pk, request.user)
        
        if not booking:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = BookingSerializer(booking)
        return Response(serializer.data)
        
    def patch(self, request, pk):
        booking = self.get_object(pk, request.user)
        
        if not booking:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Only allow status updates
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(Booking.BOOKING_STATUS):
            return Response(
                {'error': 'Valid status required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update booking status
        booking.status = new_status
        booking.save()
        
        # Add to history
        BookingHistory.objects.create(
            booking=booking,
            status=new_status,
            notes=request.data.get('notes', ''),
            created_by=request.user
        )
        
        return Response(BookingSerializer(booking).data)