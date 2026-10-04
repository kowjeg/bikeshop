from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from orders.api_views import OrderViewSet
from products.api_views import CategoryViewSet, ProductViewSet
from users.api_views import RegisterAPIView

router = DefaultRouter()

router.register('orders', OrderViewSet, basename='order')
router.register('products', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('users/register/', RegisterAPIView.as_view(), name='register'),
    path('users/login/',TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

urlpatterns += router.urls
