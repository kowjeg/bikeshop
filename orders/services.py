from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from products.models import Product

from .models import Order, OrderItem


class OrderError(Exception):
    """Любая ошибка, из-за которой заказ нельзя оформить."""


class OutOfStock(OrderError):
    pass


class InvalidQuantity(OrderError):
    pass


@transaction.atomic
def create_order(user, cart, data) -> Order:
    for item in cart:
        if item['quantity'] < 1:
            raise InvalidQuantity('В корзине некорректное количество товара. Обновите корзину.')
    total = sum(item['price'] * item['quantity'] for item in cart)

    order = Order.objects.create(user=user,
                                 status=Order.Status.PAID,
                                 total_price=total,
                                 shipping_address=(f'{data['full_name']},{data['phone_number']}\n'
                                                   f'{data['city']}, {data['address']}'

                                                   )
                                 )
    for item in cart:
        product = Product.objects.get(id=item['product_id'])
        if product.stock < item['quantity']:
            raise OutOfStock(f'Не хватает {product.name} на складе')
        product.stock -= item['quantity']
        product.save(update_fields=['stock'])

        OrderItem.objects.create(order=order, product=product, quantity=item['quantity'], price=item['price'])

    send_order_email(order)
    return order

def send_order_email(order: Order) -> None:
    send_mail(
        subject=f'bikeshop - Заказ номер {order.id}',
        message='Спасибо за заказ',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
    )
