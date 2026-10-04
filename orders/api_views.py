from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (IsAuthenticated,)


    def get_queryset(self):
        # drf_spectacular вызывает get_queryset без пользователя при генерации схемы
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return (
            Order.objects.filter(user=self.request.user)
            .select_related('user')
            .prefetch_related('items')
        )

    def get_serializer_class(self):
        return OrderCreateSerializer if self.action == 'create' else OrderSerializer


    def create(self, request, *args, **kwargs):
        write = self.get_serializer(data=request.data)
        write.is_valid(raise_exception=True)
        order = write.save()
        read = OrderSerializer(order, context=self.get_serializer_context())
        return Response(read.data, status=status.HTTP_201_CREATED)
