import pytest
from django.urls import reverse

from reviews.models import Review

pytestmark = pytest.mark.django_db


# ---------- сайт ----------

class TestProductListView:
    def test_page_opens(self, client):
        response = client.get(reverse('products:list'))
        assert response.status_code == 200

    def test_shows_only_active_products(self, client, product, inactive_product):
        response = client.get(reverse('products:list'))
        products = list(response.context['products'])
        assert product in products
        assert inactive_product not in products

    def test_search(self, client, product):
        response = client.get(reverse('products:list'), {'q': 'test_prod'})
        assert product in response.context['products']

        response = client.get(reverse('products:list'), {'q': 'nothing-like-this'})
        assert list(response.context['products']) == []

    def test_price_filter(self, client, product):
        # product стоит 5.00
        response = client.get(reverse('products:list'), {'min_price': '10'})
        assert product not in response.context['products']

        response = client.get(reverse('products:list'), {'max_price': '10'})
        assert product in response.context['products']

    def test_garbage_price_is_ignored(self, client, product):
        response = client.get(reverse('products:list'), {'min_price': 'abc'})
        assert response.status_code == 200
        assert product in response.context['products']


class TestProductDetailView:
    def test_page_opens(self, client, product):
        response = client.get(product.get_absolute_url())
        assert response.status_code == 200
        assert response.context['product'] == product

    def test_shows_reviews(self, client, product, user):
        Review.objects.create(product=product, user=user, rating=3, comments='Хороший велосипед')

        html = client.get(product.get_absolute_url()).content.decode()
        assert 'Хороший велосипед' in html
        assert html.count('fa-solid fa-star') == 3
        assert html.count('fa-regular fa-star') == 2

    def test_inactive_product_404(self, client, inactive_product):
        response = client.get(inactive_product.get_absolute_url())
        assert response.status_code == 404


# ---------- API ----------

class TestProductAPI:
    def test_list(self, api_client, product, inactive_product):
        response = api_client.get('/api/products/')
        assert response.status_code == 200
        slugs = [p['slug'] for p in response.data['results']]
        assert slugs == [product.slug]

    def test_detail_by_slug(self, api_client, product):
        response = api_client.get(f'/api/products/{product.slug}/')
        assert response.status_code == 200
        assert response.data['name'] == product.name
        assert response.data['category']['slug'] == product.category.slug

    def test_inactive_detail_404(self, api_client, inactive_product):
        response = api_client.get(f'/api/products/{inactive_product.slug}/')
        assert response.status_code == 404

    def test_read_only(self, auth_api_client, product):
        response = auth_api_client.delete(f'/api/products/{product.slug}/')
        assert response.status_code == 405


class TestCategoryAPI:
    def test_list(self, api_client, category):
        response = api_client.get('/api/categories/')
        assert response.status_code == 200
        assert response.data['results'][0]['slug'] == category.slug
