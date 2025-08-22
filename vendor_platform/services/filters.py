from django_filters import rest_framework as filters
from vendors.models import Vendor, VendorService

class VendorFilter(filters.FilterSet):
    min_rating = filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = filters.NumberFilter(field_name='rating', lookup_expr='lte')
    service_category = filters.CharFilter(field_name='services__category__name', lookup_expr='iexact')
    city = filters.CharFilter(field_name='city', lookup_expr='iexact')
    state = filters.CharFilter(field_name='state', lookup_expr='iexact')
    price_min = filters.NumberFilter(field_name='services__base_price', lookup_expr='gte')
    price_max = filters.NumberFilter(field_name='services__base_price', lookup_expr='lte')
    
    class Meta:
        model = Vendor
        fields = ['min_rating', 'max_rating', 'service_category', 'city', 'state', 'price_min', 'price_max']
        
class VendorSearchView(generics.ListAPIView):
    queryset = Vendor.objects.filter(status='approved').prefetch_related('services')
    serializer_class = VendorProfileSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = VendorFilter
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search by company name or description
        search_query = self.request.query_params.get('q')
        if search_query:
            queryset = queryset.filter(
                models.Q(company_name__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
            
        # Ordering
        ordering = self.request.query_params.get('ordering')
        if ordering:
            if ordering == 'rating':
                queryset = queryset.order_by('-rating', '-total_reviews')
            elif ordering == 'price_low':
                queryset = queryset.annotate(
                    min_price=models.Min('services__base_price')
                ).order_by('min_price')
            elif ordering == 'price_high':
                queryset = queryset.annotate(
                    min_price=models.Min('services__base_price')
                ).order_by('-min_price')
                
        return queryset