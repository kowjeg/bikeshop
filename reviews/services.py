from orders.models import Order, OrderItem

from .models import Review


def has_purchased(user, product) -> bool:
    """Есть ли у пользователя неотменённый заказ с этим товаром."""
    if not user.is_authenticated:
        return False

    return (
        OrderItem.objects
        .filter(order__user=user, product=product)
        .exclude(order__status=Order.Status.CANCELLED)
        .exists()
    )


def can_review(user, product) -> bool:
    """Можно ли пользователю оставить отзыв: купил и ещё не писал."""
    if not has_purchased(user, product):
        return False

    return not Review.objects.filter(user=user, product=product).exists()