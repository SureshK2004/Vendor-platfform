from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.db import transaction
from django.conf import settings
import jwt
from datetime import datetime, timedelta

from .models import Vendor, VendorService, PricingTier, AvailabilitySlot
from .serializers import (
    VendorRegistrationSerializer, VendorLoginSerializer, 
    VendorProfileSerializer, VendorServiceSerializer,
    AvailabilitySlotSerializer, PricingTierSerializer
)
from utils.throttling import VendorThrottle
from authentication.utils import generate_jwt_token  # add this import

class VendorLoginView(APIView):
    def post(self, request):
        serializer = VendorLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT token using our utility function
            token = generate_jwt_token(user)
            
            return Response({
                'token': token,
                'vendor': VendorProfileSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VendorRegistrationView(APIView):
    throttle_classes = [VendorThrottle]
    
    def post(self, request):
        serializer = VendorRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            with transaction.atomic():
                vendor = serializer.save()
                
            # In a real implementation, you would send an email for verification
            # and admin approval here
            
            return Response({
                'message': 'Vendor registration successful. Awaiting approval.',
                'vendor_id': vendor.vendor_id
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class VendorProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = VendorProfileSerializer(request.user)
        return Response(serializer.data)
        
    def put(self, request):
        serializer = VendorProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class VendorServiceListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, request):
        services = VendorService.objects.filter(vendor=request.user, is_active=True)
        serializer = VendorServiceSerializer(services, many=True)
        return Response(serializer.data)
        
    def post(self, request):
        serializer = VendorServiceSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(vendor=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class VendorServiceDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self, pk, vendor):
        try:
            return VendorService.objects.get(pk=pk, vendor=vendor)
        except VendorService.DoesNotExist:
            return None
            
    def get(self, request, pk):
        service = self.get_object(pk, request.user)
        
        if not service:
            return Response(
                {'error': 'Service not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = VendorServiceSerializer(service)
        return Response(serializer.data)
        
    def put(self, request, pk):
        service = self.get_object(pk, request.user)
        
        if not service:
            return Response(
                {'error': 'Service not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = VendorServiceSerializer(service, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk):
        service = self.get_object(pk, request.user)
        
        if not service:
            return Response(
                {'error': 'Service not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Soft delete by marking as inactive
        service.is_active = False
        service.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
class AvailabilitySlotView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        service_id = request.query_params.get('service_id')
        
        slots = AvailabilitySlot.objects.filter(vendor=request.user)
        
        if date_from:
            slots = slots.filter(date__gte=date_from)
            
        if date_to:
            slots = slots.filter(date__lte=date_to)
            
        if service_id:
            slots = slots.filter(service_id=service_id)
            
        serializer = AvailabilitySlotSerializer(slots, many=True)
        return Response(serializer.data)
        
    def post(self, request):
        serializer = AvailabilitySlotSerializer(
            data=request.data, 
            context={'vendor': request.user}
        )
        
        if serializer.is_valid():
            serializer.save(vendor=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)