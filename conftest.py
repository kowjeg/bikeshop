from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from products.models import Category, Product

User = get_user_model()

PASSWORD = 'SecretKey123'


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@test.ru',
        password=PASSWORD,
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(
        username='otheruser',
        email='other@test.ru',
        password=PASSWORD,
    )


@pytest.fixture
def category():
    return Category.objects.create(
        name='test_cat',
        slug='test_cat',
    )


@pytest.fixture
def product(category):
    return Product.objects.create(
        name='test_prod',
        slug='test_prod',
        description='test_prod',
        price=Decimal('5.00'),
        category=category,
        stock=10,
    )


@pytest.fixture
def inactive_product(category):
    return Product.objects.create(
        name='hidden_prod',
        slug='hidden_prod',
        price=Decimal('7.00'),
        category=category,
        stock=10,
        is_active=False,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_api_client(api_client, user):
    """API-клиент, авторизованный как user (без JWT — для тестов это не важно)."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def logged_client(client, user):
    """Обычный Django-клиент для сайта, залогиненный как user."""
    client.force_login(user)
    return client
