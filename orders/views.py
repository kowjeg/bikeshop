from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import Product

from .cart import Cart
from .forms import CheckoutForm
from .services import OrderError, create_order

# Create your views here.

def parse_quantity(request):
    """Достаёт quantity из формы. Если там не число, возвращает None."""
    try:
        return int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        return None


def cart_detail(request):
    return render(request, 'cart.html', {'cart': Cart(request)})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    quantity = parse_quantity(request)
    if quantity is None or quantity < 1:
        messages.error(request, 'Количество должно быть целым числом не меньше 1.')
        return redirect('orders:cart_detail')

    already = next((item['quantity'] for item in cart if item['product'].id == product_id), 0)

    if already + quantity > product.stock:
        messages.error(request, f'Только {product.stock} шт {product.name} в наличии.')
        return redirect('orders:cart_detail')

    cart.add(product, quantity)
    messages.success(request, f'{product.name} добавлен в корзину.')
    return redirect('orders:cart_detail')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    quantity = parse_quantity(request)
    if quantity is None:
        messages.error(request, 'Количество должно быть целым числом.')
        return redirect('orders:cart_detail')

    if quantity < 1:
        cart.remove(product)

    elif quantity > product.stock:
        messages.error(request, f'Только {product.stock} шт. в наличии')
    else:
        cart.add(product, quantity, override=True)

    return redirect('orders:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart.remove(product)
    messages.info(request, f'{product.name} удален из корзины')
    return redirect('orders:cart_detail')


@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, 'Корзина пуста!')
        return redirect('products:list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            cart_data = [
                {
                    'product_id': item['product'].id,
                    'quantity': item['quantity'],
                    'price': item['price'],
                }
                for item in cart
            ]
            try:
                create_order(request.user, cart_data, form.cleaned_data)
            except OrderError as e:
                messages.error(request, str(e))
                return redirect('orders:cart_detail')

            cart.clear()
            messages.success(request, 'Заказ оформлен!')
            return redirect('products:list')
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {'form': form, 'cart': cart})
