from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from products.models import Product
from .cart import Cart
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