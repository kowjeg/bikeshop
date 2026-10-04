from django.db.models import Avg
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Product, Category
from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filterset_fields = ['category__name']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'avg_rating']


    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related('category')
            .annotate(avg_rating=Avg('reviews__rating'))
            .order_by('created_at')
        )

