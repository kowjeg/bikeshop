from decimal import Decimal

import pytest
from django.core import mail
from django.urls import reverse

from orders.cart import CART_SESSION_ID
from orders.models import Order

pytestmark = pytest.mark.django_db


CHECKOUT_DATA = {
    'full_name': 'Иван Иванов',
    'phone_number': '+79990000000',
    'city': 'Москва',
    'address': 'ул. Пушкина, 1',
    'payment_type': 'cod',
}


def add_to_cart(client, product, quantity=1):
    return client.post(
        reverse('orders:cart_add', args=[product.id]),
        {'quantity': quantity},
    )


# ---------- корзина ----------

class TestCart:
    def test_cart_page_opens(self, client):
        response = client.get(reverse('orders:cart_detail'))
        assert response.status_code == 200

    def test_add(self, client, product):
        response = add_to_cart(client, product, 2)
        assert response.status_code == 302
        assert client.session[CART_SESSION_ID][str(product.id)]['quantity'] == 2

    def test_add_more_than_stock(self, client, product):
        add_to_cart(client, product, product.stock + 1)
        assert str(product.id) not in client.session.get(CART_SESSION_ID, {})

    def test_add_only_post(self, client, product):
        response = client.get(reverse('orders:cart_add', args=[product.id]))
        assert response.status_code == 405

    def test_remove(self, client, product):
        add_to_cart(client, product)
        client.post(reverse('orders:cart_remove', args=[product.id]))
        assert str(product.id) not in client.session[CART_SESSION_ID]

    def test_update(self, client, product):
        add_to_cart(client, product, 1)
        client.post(reverse('orders:cart_update', args=[product.id]), {'quantity': 3})
        assert client.session[CART_SESSION_ID][str(product.id)]['quantity'] == 3


# ---------- оформление заказа на сайте ----------

class TestCheckout:
    def test_requires_login(self, client):
        response = client.get(reverse('orders:checkout'))
        assert response.status_code == 302
        assert reverse('users:login') in response.url

    def test_empty_cart_redirects(self, logged_client):
        response = logged_client.get(reverse('orders:checkout'))
        assert response.status_code == 302
        assert response.url == reverse('products:list')

    def test_creates_order(self, logged_client, user, product):
        add_to_cart(logged_client, product, 2)

        response = logged_client.post(reverse('orders:checkout'), CHECKOUT_DATA)

        assert response.status_code == 302
        order = Order.objects.get(user=user)
        assert order.total_price == Decimal('10.00')
        assert order.items.count() == 1

        product.refresh_from_db()
        assert product.stock == 8

        assert CART_SESSION_ID not in logged_client.session
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [user.email]


# ---------- API ----------

class TestOrderAPI:
    url = '/api/orders/'

    def test_requires_auth(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_create(self, auth_api_client, user, product):
        payload = {
            'shipping_address': 'Москва',
            'items': [{'product_id': product.id, 'quantity': 3}],
        }
        response = auth_api_client.post(self.url, payload, format='json')

        assert response.status_code == 201
        assert Decimal(response.data['total_price']) == Decimal('15.00')
        assert Order.objects.filter(user=user).count() == 1

        product.refresh_from_db()
        assert product.stock == 7

    def test_not_enough_stock(self, auth_api_client, product):
        payload = {
            'shipping_address': 'Москва',
            'items': [{'product_id': product.id, 'quantity': product.stock + 1}],
        }
        response = auth_api_client.post(self.url, payload, format='json')

        assert response.status_code == 400
        assert Order.objects.count() == 0  # транзакция откатилась

        product.refresh_from_db()
        assert product.stock == 10

    def test_unknown_product(self, auth_api_client):
        payload = {
            'shipping_address': 'Москва',
            'items': [{'product_id': 999999, 'quantity': 1}],
        }
        response = auth_api_client.post(self.url, payload, format='json')
        assert response.status_code == 400

    def test_empty_items(self, auth_api_client):
        payload = {'shipping_address': 'Москва', 'items': []}
        response = auth_api_client.post(self.url, payload, format='json')
        assert response.status_code == 400

    def test_user_sees_only_own_orders(self, auth_api_client, user, other_user):
        Order.objects.create(user=user, total_price=1)
        foreign = Order.objects.create(user=other_user, total_price=1)

        response = auth_api_client.get(self.url)
        assert response.status_code == 200
        assert response.data['count'] == 1

        response = auth_api_client.get(f'{self.url}{foreign.id}/')
        assert response.status_code == 404
