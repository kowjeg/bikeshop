from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from products.models import Product
from .cart import Cart
from .forms import CheckoutForm
from .services import create_order, OutOfStock
# Create your views here.

def cart_detail(request):
    return render(request, 'cart.html', {'cart': Cart(request)})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    quantity = int(request.POST.get('quantity',1))

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
    quantity = int(request.POST.get('quantity',1))

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
            except OutOfStock as e:
                messages.error(request, str(e))
                return redirect('orders:cart_detail')

            cart.clear()
            messages.success(request, 'Заказ оформлен!')
            return redirect('products:list')
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {'form': form, 'cart': cart})