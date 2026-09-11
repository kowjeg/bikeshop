from decimal import Decimal

from django.contrib.sites import requests

from products.models import Product


CART_SESSION_ID = 'cart'

class Cart:
    """Корзина, живущая в сессии пользователя"""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)

        if cart is None:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart


    def add(self, product, quantity = 1, override=False ):

        pid = str(product.id)
        if pid not in self.cart:
            self.cart[pid] = {'quantity': 0, 'price': str(product.price)}
        if override:
            self.cart[pid]['quantity'] += quantity
        else:
            self.cart[pid]['quantity'] += quantity

        self.save()

    def remove(self, product):
        pid = str(product.id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()


    def save(self):
        self.session.modified = True

    def __iter__(self):
        products = Product.objects.filter(id__in = self.cart.keys())
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item


    def __len__(self):
        return len(self.cart)

    def get_total_price(self):
        total_price = 0
        for product in self.cart.values():
            total_price += product['price'] * product['quantity']
        return total_price

    def clear(self):
        del self.session[CART_SESSION_ID]
        self.save()