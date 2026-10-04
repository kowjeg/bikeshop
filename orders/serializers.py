from rest_framework import serializers
from .models import Order, OrderItem
from .services import send_order_email
from products.models import Product

from django.db import transaction


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'items', 'user', 'status', 'total_price', 'shipping_address', 'created_at']


class OrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    shipping_address = serializers.CharField()
    items = OrderItemWriteSerializer(many=True, allow_empty=False)

    def validate_items(self, items):
        product_ids = [item['product_id'] for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError('Один товар указан несколько раз')

        existing = set(
            Product.objects.filter(id__in=product_ids, is_active=True).values_list('id', flat=True)
        )
        missing = [pid for pid in product_ids if pid not in existing]
        if missing:
            raise serializers.ValidationError(f'Товары не найдены: {missing}')
        return items

    def create(self, validated_data):
        user = self.context['request'].user
        quantities = {item['product_id']: item['quantity'] for item in validated_data['items']}

        with transaction.atomic():
            # select_for_update блокирует строки товаров до конца транзакции,
            # чтобы два одновременных заказа не списали один и тот же остаток
            products = Product.objects.select_for_update().filter(id__in=quantities).order_by('id')

            order = Order.objects.create(
                user=user,
                status=Order.Status.PAID,
                total_price=0,
                shipping_address=validated_data['shipping_address'],
            )
            total = 0

            for product in products:
                quantity = quantities[product.id]
                if product.stock < quantity:
                    raise serializers.ValidationError(f'Не хватает {product.name} на складе')

                product.stock -= quantity
                product.save(update_fields=['stock'])

                OrderItem.objects.create(order=order, product=product, quantity=quantity, price=product.price)
                total += quantity * product.price

            order.total_price = total
            order.save(update_fields=['total_price'])

            transaction.on_commit(lambda: send_order_email(order))

        return order
